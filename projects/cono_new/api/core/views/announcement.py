"""系统公告 / 通知。

读取（列表、未读数、标记已读）对所有登录用户开放——公告本来就是给全员看的，
要求 announcement_list 权限会导致普通账号看不到公告。
发布/编辑/删除才校验 announcement_* 权限码。
"""
from rest_framework.decorators import action
from rest_framework.response import Response

from api.core import models
from api.core.permissions import get_effective_permissions
from api.core.serializers.common import AnnouncementSerializer
from api.core.views.base import BaseModelViewSet

MANAGE_PERMS = {'announcement_add', 'announcement_edit', 'announcement_delete'}


class AnnouncementViewSet(BaseModelViewSet):
    queryset = models.Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_codes = 'announcement_list'
    action_permission_codes = {
        # 全员可读，不校验权限码
        'list': [], 'retrieve': [], 'unread_count': [],
        'mark_read': [], 'mark_all_read': [],
    }

    def _can_manage(self):
        user = self.request.user
        if getattr(user, 'role', '') == 'admin':
            return True
        return bool(MANAGE_PERMS & (get_effective_permissions(user) or set()))

    def get_queryset(self):
        qs = super().get_queryset()
        # 公告管理页要能看到已下架的，普通用户只看已发布的。
        # 用权限判断而不是只认参数，避免普通用户传 include_inactive 绕过。
        if self.request.query_params.get('include_inactive') in ('1', 'true', 'True') and self._can_manage():
            return qs
        return qs.filter(is_active=True)

    def _read_ids(self, qs=None):
        reads = models.AnnouncementRead.objects.filter(user=self.request.user)
        if qs is not None:
            reads = reads.filter(announcement__in=qs)
        return set(reads.values_list('announcement_id', flat=True))

    def _unread_total(self, qs=None):
        qs = self.get_queryset() if qs is None else qs
        return max(qs.count() - len(self._read_ids(qs)), 0)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['read_ids'] = self._read_ids()
        return ctx

    def perform_create(self, serializer):
        serializer.save(publisher=self.request.user)

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
