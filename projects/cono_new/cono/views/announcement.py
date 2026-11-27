"""老版系统的公告 / 通知接口（JSON，供 layout.html 的铃铛调用）。

公告数据与新版共用同一张表，因此新版发布的通知在老版同样能看到。
读取对全部登录用户开放（公告本就是给全员看的），标记已读只影响当前用户。
"""
import re
from urllib.parse import quote

from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from cono import models
from cono.tools.form import AnnouncementForm


def _published():
    return models.Announcement.objects.filter(
        is_active=True, is_delete=False).prefetch_related('attachments')


def _read_ids(user_id):
    return set(
        models.AnnouncementRead.objects
        .filter(user_id=user_id, announcement__in=_published())
        .values_list('announcement_id', flat=True)
    )


def _unread_total(user_id):
    return max(_published().count() - len(_read_ids(user_id)), 0)


def _serialize(item, read_ids):
    return {
        'id': item.id,
        'title': item.title,
        'content': item.content,
        'kind': item.kind,
        'kind_display': item.get_kind_display(),
        'is_top': item.is_top,
        'publisher': item.publisher.username if item.publisher else '',
        # 与新版前端 formatTime 保持一致的本地时间字符串
        'publish_time': item.publish_time.strftime('%Y-%m-%d %H:%M'),
        'is_read': item.id in read_ids,
        'attachments': [
            {
                'id': att.id,
                'name': att.name or att.file.name.rsplit('/', 1)[-1],
                'size': att.size,
                'url': '/announcement/{}'.format(att.download_path),
            }
            for att in item.attachments.all()
        ],
    }


@require_GET
def announcement_list(request):
    """未读数 + 公告列表，一次返回，避免铃铛打开时发两个请求。

    带 count=1 时只返回未读数，供定时轮询使用——轮询不该每次都拉全文。
    """
    user_id = request.info_dict_useid
    if request.GET.get('count') == '1':
        return JsonResponse({'unread': _unread_total(user_id)})
    read_ids = _read_ids(user_id)
    items = [_serialize(item, read_ids) for item in _published()]
    return JsonResponse({'unread': _unread_total(user_id), 'results': items})


@require_POST
def announcement_read(request, nid):
    """标记单条已读。重复调用幂等。"""
    user_id = request.info_dict_useid
    if not _published().filter(id=nid).exists():
        return JsonResponse({'detail': '公告不存在或已下架'}, status=404)
    models.AnnouncementRead.objects.get_or_create(announcement_id=nid, user_id=user_id)
    return JsonResponse({'unread': _unread_total(user_id)})


@require_POST
def announcement_read_all(request):
    user_id = request.info_dict_useid
    read_ids = _read_ids(user_id)
    pending = [a for a in _published() if a.id not in read_ids]
    models.AnnouncementRead.objects.bulk_create(
        [models.AnnouncementRead(announcement=a, user_id=user_id) for a in pending],
        ignore_conflicts=True,
    )
    return JsonResponse({'unread': 0, 'marked': len(pending)})


# ===== 公告管理（老版页面，与新版共用同一张表） =====

def announcement_manage_list(request):
    """公告管理列表：管理员能看到已下架的公告。"""
    title = '公告管理'
    queryset = models.Announcement.objects.filter(is_delete=False).select_related('publisher')
    keyword = (request.GET.get('keyword') or '').strip()
    if keyword:
        queryset = queryset.filter(title__icontains=keyword)
    return render(request, 'announcement/announcement_list.html', {
        'title': title,
        'queryset': queryset,
        'keyword': keyword,
    })


def _bind_attachments(announcement, extra_tokens=()):
    """把草稿附件绑定到本条公告。

    与新版 AnnouncementViewSet._bind_attachments 同一规则：正文里的 token 一定
    绑上；另外接收表单提交的隐藏字段，兜底「上传了但没插链接」的情况。老版插入
    的是 /announcement/... 链接，新版插的是 /api/announcement/...，正则都能匹配。
    """
    tokens = set(re.findall(
        r'/attachment/([0-9a-fA-F-]{36})/download/', announcement.content or ''))
    tokens.update(t for t in extra_tokens if t)
    if not tokens:
        return
    models.AnnouncementAttachment.objects.filter(
        token__in=tokens,
    ).filter(
        Q(announcement__isnull=True) | Q(announcement=announcement),
    ).update(announcement=announcement)


def _announcement_form(request, instance=None):
    title = '修改公告' if instance else '发布公告'
    if request.method == 'GET':
        form = AnnouncementForm(instance=instance)
        return render(request, 'announcement/announcement_form.html',
                      {'form': form, 'title': title, 'instance': instance})

    form = AnnouncementForm(data=request.POST, instance=instance)
    if form.is_valid():
        obj = form.save(commit=False)
        if instance is None:
            obj.publisher_id = request.info_dict_useid
        obj.save()
        _bind_attachments(obj, request.POST.getlist('attachment_tokens'))
        messages.success(request, '公告已保存')
        return redirect('/announcement/list/')
    return render(request, 'announcement/announcement_form.html',
                  {'form': form, 'title': title, 'instance': instance})


def announcement_add(request):
    return _announcement_form(request)


def announcement_edit(request, nid):
    instance = models.Announcement.objects.filter(id=nid, is_delete=False).first()
    if instance is None:
        return redirect('/announcement/list/')
    return _announcement_form(request, instance)


@require_POST
def announcement_attachment_upload(request):
    """老版公告附件上传。返回 JSON，供表单页的 JS 插入链接。"""
    f = request.FILES.get('file')
    if not f:
        return JsonResponse({'detail': '请选择文件'}, status=400)
    if f.size > 50 * 1024 * 1024:
        return JsonResponse({'detail': '附件不能超过 50MB'}, status=400)

    att = models.AnnouncementAttachment.objects.create(
        file=f, name=f.name.rsplit('/', 1)[-1][:255], size=f.size)
    return JsonResponse({
        'id': att.id,
        'token': str(att.token),
        'name': att.name,
        'size': att.size,
        'download_url': '/announcement/{}'.format(att.download_path),
    }, status=201)


@require_http_methods(['POST', 'DELETE'])
def announcement_attachment_delete(request, token):
    """删除尚未绑定公告的草稿附件。"""
    att = models.AnnouncementAttachment.objects.filter(token=token).first()
    if att is None:
        raise Http404('附件不存在')
    if att.announcement_id:
        return JsonResponse({'detail': '该附件已随公告发布，不能单独删除'}, status=400)
    att.file.delete(save=False)
    att.delete()
    return JsonResponse({'ok': True})


@require_GET
def announcement_attachment_download(request, token):
    """老版的附件下载入口。

    新版正文里插的是 /api/announcement/attachment/<token>/download/，但老版
    8000 没有 /api 路由，直接点会 404。这里按 token 提供同样能力，老版页面
    渲染附件时会指向本视图。
    """
    att = models.AnnouncementAttachment.objects.filter(token=token).first()
    if att is None or not att.file:
        raise Http404('附件不存在')
    # 与新版一致：已绑定到公告的，公告下架后链接失效；草稿附件仍可下载
    # （token 不可猜，上传后到保存公告之间需要能预览）。
    if att.announcement_id and not (
            att.announcement.is_active and not att.announcement.is_delete):
        raise Http404('附件不存在')
    try:
        fh = att.file.open('rb')
    except (FileNotFoundError, OSError):
        raise Http404('附件文件已丢失')

    models.AnnouncementAttachment.objects.filter(pk=att.pk).update(
        download_count=models.F('download_count') + 1)

    name = att.name or att.file.name.rsplit('/', 1)[-1]
    resp = FileResponse(fh, as_attachment=True, filename=name)
    resp['Content-Disposition'] = "attachment; filename*=UTF-8''{}".format(quote(name))
    return resp


@require_POST
def announcement_delete(request):
    """软删除公告。已读记录随 is_delete 一起失效，不需要额外清理。"""
    nid = request.POST.get('nid')
    obj = models.Announcement.objects.filter(id=nid, is_delete=False).first()
    if obj is None:
        messages.error(request, '公告不存在')
        return redirect('/announcement/list/')
    obj.is_delete = True
    obj.save(update_fields=['is_delete', 'update_time'])
    messages.success(request, '公告已删除')
    return redirect('/announcement/list/')
