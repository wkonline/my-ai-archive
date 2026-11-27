"""系统公告 / 通知。

读取（列表、未读数、标记已读）对所有登录用户开放——公告本来就是给全员看的，
要求 announcement_list 权限会导致普通账号看不到公告。
发布/编辑/删除才校验 announcement_* 权限码。
"""
import os
import re

from django.db.models import Q
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from urllib.parse import quote

from api.core import models
from api.core.permissions import get_effective_permissions
from api.core.serializers.common import AnnouncementAttachmentSerializer, AnnouncementSerializer
from api.core.views.base import BaseModelViewSet

MANAGE_PERMS = {'announcement_add', 'announcement_edit', 'announcement_delete'}

# 单个附件上限。公告附件多是手册、制度文件，给到 50MB；再大应该走共享盘。
MAX_ATTACHMENT_SIZE = 50 * 1024 * 1024


class AnnouncementViewSet(BaseModelViewSet):
    queryset = models.Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_codes = 'announcement_list'
    action_permission_codes = {
        # 全员可读，不校验权限码
        'list': [], 'retrieve': [], 'unread_count': [],
        'mark_read': [], 'mark_all_read': [],
        # 附件下载同样对全员开放：公告正文里的链接点开就要能下
        'download_attachment': [],
    }

    def _can_manage(self):
        user = self.request.user
        if getattr(user, 'role', '') == 'admin':
            return True
        return bool(MANAGE_PERMS & (get_effective_permissions(user) or set()))

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('attachments')
        # 公告管理页要能看到已下架的，普通用户只看已发布的。
        # 用权限判断而不是只认参数，避免普通用户传 include_inactive 绕过。
        if self.request.query_params.get('include_inactive') in ('1', 'true', 'True') and self._can_manage():
            return qs
        return qs.filter(is_active=True)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['read_ids'] = self._read_ids()
        # 列表页每条公告都带附件，不预取会变成 N+1 次查询
        ctx['request'] = self.request
        return ctx

    def _read_ids(self, qs=None):
        reads = models.AnnouncementRead.objects.filter(user=self.request.user)
        if qs is not None:
            reads = reads.filter(announcement__in=qs)
        return set(reads.values_list('announcement_id', flat=True))

    def _unread_total(self, qs=None):
        qs = self.get_queryset() if qs is None else qs
        return max(qs.count() - len(self._read_ids(qs)), 0)

    def perform_create(self, serializer):
        announcement = serializer.save(publisher=self.request.user)
        self._bind_attachments(announcement)

    def perform_update(self, serializer):
        announcement = serializer.save()
        self._bind_attachments(announcement)

    def _bind_attachments(self, announcement):
        """把草稿附件绑定到本条公告。

        上传时公告还没有 id，附件先以 announcement=None 落库。绑定的来源有两个：
        正文里 /attachment/<token>/download/ 形式的链接，以及前端显式提交的
        attachment_tokens。前者覆盖「在正文里插入了链接」的常规路径，后者兜底
        「上传了但没插链接」——用户既然在本次编辑里选了文件，就不该让它悄悄消失。
        """
        tokens = set(re.findall(
            r'/attachment/([0-9a-fA-F-]{36})/download/', announcement.content or ''))
        tokens.update(self._requested_attachment_tokens())
        if not tokens:
            return
        # 只收无主附件或本公告自己的附件，避免把别人公告的附件抢过来
        models.AnnouncementAttachment.objects.filter(
            token__in=tokens,
        ).filter(
            Q(announcement__isnull=True) | Q(announcement=announcement),
        ).update(announcement=announcement)

    def _requested_attachment_tokens(self):
        raw = self.request.data.get('attachment_tokens') or []
        if isinstance(raw, str):
            raw = [raw]
        tokens = set()
        for item in raw:
            value = str(item).strip()
            if re.fullmatch(r'[0-9a-fA-F-]{36}', value):
                tokens.add(value)
        return tokens

    @action(detail=False, methods=['post'], url_path='upload-attachment')
    def upload_attachment(self, request):
        """上传公告附件，返回可插入正文的下载地址。

        不校验 announcement_add 权限码以外的东西，但必须能管理公告——
        普通用户不该往公告里塞文件。
        """
        if not self._can_manage():
            return Response({'detail': '没有发布公告的权限'}, status=status.HTTP_403_FORBIDDEN)

        f = request.FILES.get('file')
        if not f:
            return Response({'detail': '请选择文件'}, status=status.HTTP_400_BAD_REQUEST)
        if f.size > MAX_ATTACHMENT_SIZE:
            return Response(
                {'detail': '附件不能超过 {}MB'.format(MAX_ATTACHMENT_SIZE // 1024 // 1024)},
                status=status.HTTP_400_BAD_REQUEST)

        att = models.AnnouncementAttachment.objects.create(
            file=f,
            name=os.path.basename(f.name)[:255],
            size=f.size,
        )
        return Response(AnnouncementAttachmentSerializer(att).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'],
            url_path=r'attachment/(?P<token>[0-9a-fA-F-]{36})/download',
            authentication_classes=[], permission_classes=[])
    def download_attachment(self, request, token=None):
        """按 token 下载附件。

        免登录：正文里的链接是普通 <a>，浏览器点开不会带 Authorization 头，
        要求认证就永远下不动。token 是 uuid4，猜不到，等价于一次性能力链接；
        附件本身也只是公告里的公开文件。
        """
        att = models.AnnouncementAttachment.objects.filter(token=token).first()
        if att is None or not att.file:
            raise Http404('附件不存在')
        # 公告下架或删除后链接失效，避免旧链接长期可下
        if att.announcement_id and not (
                att.announcement.is_active and not att.announcement.is_delete):
            raise Http404('附件不存在')

        try:
            fh = att.file.open('rb')
        except (FileNotFoundError, OSError):
            raise Http404('附件文件已丢失')

        models.AnnouncementAttachment.objects.filter(pk=att.pk).update(
            download_count=models.F('download_count') + 1)

        name = att.name or os.path.basename(att.file.name)
        resp = FileResponse(fh, as_attachment=True, filename=name)
        # FileResponse 的 filename 走 RFC 5987 编码，中文名需要显式补 filename*
        resp['Content-Disposition'] = "attachment; filename*=UTF-8''{}".format(quote(name))
        return resp

    @action(detail=False, methods=['delete'],
            url_path=r'attachment/(?P<token>[0-9a-fA-F-]{36})')
    def delete_attachment(self, request, token=None):
        """删除附件。只能删草稿附件，已发布的走公告编辑页管理。"""
        if not self._can_manage():
            return Response({'detail': '没有管理公告的权限'}, status=status.HTTP_403_FORBIDDEN)
        att = models.AnnouncementAttachment.objects.filter(token=token).first()
        if att is None:
            return Response({'detail': '附件不存在'}, status=status.HTTP_404_NOT_FOUND)
        if att.announcement_id:
            return Response({'detail': '该附件已随公告发布，请在公告编辑页处理'},
                            status=status.HTTP_400_BAD_REQUEST)
        att.file.delete(save=False)
        att.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        return Response({'unread': self._unread_total()})

    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        models.AnnouncementRead.objects.get_or_create(
            announcement=self.get_object(), user=request.user)
        return Response({'unread': self._unread_total()})

    @action(detail=False, methods=['post'], url_path='read-all')
    def mark_all_read(self, request):
        qs = self.get_queryset()
        pending = [a for a in qs if a.id not in self._read_ids(qs)]
        models.AnnouncementRead.objects.bulk_create(
            [models.AnnouncementRead(announcement=a, user=request.user) for a in pending],
            ignore_conflicts=True,
        )
        return Response({'unread': 0, 'marked': len(pending)})
