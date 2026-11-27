"""老版系统的公告 / 通知接口（JSON，供 layout.html 的铃铛调用）。

公告数据与新版共用同一张表，因此新版发布的通知在老版同样能看到。
读取对全部登录用户开放（公告本就是给全员看的），标记已读只影响当前用户。
"""
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from cono import models
from cono.tools.form import AnnouncementForm


def _published():
    return models.Announcement.objects.filter(is_active=True, is_delete=False)


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
