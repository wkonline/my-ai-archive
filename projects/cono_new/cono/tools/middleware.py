import re

from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib.auth.models import AnonymousUser
from cono import models
from cono.tools.auth_profile import get_session_permissions
from cono.tools.user_log_cleanup import cleanup_expired_user_logs_daily


# 某些路由的 url_name 与其应校验的权限码不一致（历史命名遗留）。
# 在这里做一次映射，避免因为“同名不同义”导致越权或误拦截。
URL_PERMISSION_ALIASES = {
    # 合同产品明细使用既有的 contract_product 权限，而非产品型号的 product_list
    'contract_product_list': 'contract_product',
}


def _permission_candidates(url_name):
    """某个 url_name 可接受的全部权限码。

    建单路由在 URL 里叫 *_create（如 contract_create），而权限码习惯用 *_add，
    两套命名历史上并存，任一方有权限都应放行，否则会出现「有 contract_add 却建不了合同」。
    """
    code = URL_PERMISSION_ALIASES.get(url_name, url_name)
    codes = {code}
    for suffix, other in (('_create', '_add'), ('_add', '_create')):
        if code.endswith(suffix):
            codes.add(code[:-len(suffix)] + other)
    return codes


def _is_attachment_download(path):
    """公告附件下载路径：/announcement/attachment/<uuid>/download/"""
    return bool(re.match(
        r'^/announcement/attachment/[0-9a-fA-F-]{36}/download/?$', path or ''))


class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 1.不用登录就可以访问处理
        if request.path_info in ["/login/", "/image/code/","/register/", "/dify/search/"]:
            return
        # 公告附件下载：正文里是普通 <a>，点开不带 session，要求登录就下不动。
        # token 是 uuid4，猜不到，等同于带能力的一次性链接。
        if _is_attachment_download(request.path_info):
            return
        # 2.获取session
        info_dict = request.session.get("info")
        # 未登录
        if not info_dict:
            return redirect('/login/')

        # 已登录
        request.info_dict_useid=info_dict['id']
        request.info_dict_username=info_dict['username']
        request.info_dict_role=info_dict['role']
        # 角色可被管理员随时改到别的角色，session 里的旧角色会让权限滞后到下次登录。
        # 这里以库里的当前角色为准（顺带处理账号被删除的情况）。
        current = models.User.objects.filter(id=request.info_dict_useid).values('role').first()
        if current is None:
            request.session.clear()
            return redirect('/login/')
        if current['role'] != info_dict['role']:
            request.info_dict_role = current['role']
            info_dict['role'] = current['role']
            request.session['info'] = info_dict
            request.session.modified = True
        cleanup_expired_user_logs_daily()
        models.UserLog.objects.create(user_id=request.info_dict_useid,
                                      action=request.path,
                                      ip=request.META.get('REMOTE_ADDR')
                                      )
        return

    def process_view(self, request, view_func, args, kwargs):
        if _is_attachment_download(request.path_info):
            return
        if request.path_info in [
            '/login/', '/logout/', '/image/code/', '/',
            '/ajax/search-companys/', '/ajax/check-contract-number/',
            '/ajax/delivery-customer-info/', '/ajax/get-plan-contract-products/',
            '/register/', '/dify/search/',
        ]:
            return
        # 1.当前用户角色
        role = request.info_dict_role
        # 管理员放行全部功能（与新版 API 的 HasPermission 保持一致）。
        # 否则新增权限码只写进 settings、没同步到 auth_role 表时，管理员会被自己挡在门外。
        if role == 'admin':
            return
        # 2.允许用户修改/重置自己的资料和密码
        url_name = request.resolver_match.url_name
        # 公告对全员可见：读取、标记已读都不校验权限码（公告本就是给全员看的）
        if url_name in ('announcement_list', 'announcement_read', 'announcement_read_all'):
            return
        if url_name in ('user_edit', 'user_reset', 'user_profile', 'user_profile_edit', 'user_change_password'):
            target_id = kwargs.get('nid')
            if target_id is not None and int(target_id) == request.info_dict_useid:
                return
        if url_name in ('user_profile', 'user_profile_edit', 'user_change_password'):
            return
        # 2.自己具备的权限
        user_permission_set = get_session_permissions(role, request.info_dict_useid)
        if url_name == 'service_copy' and (
            'service_add' in user_permission_set or 'service_edit' in user_permission_set
        ):
            return
        if url_name == 'servicedetail_batch_add' and (
            'servicedetail_add' in user_permission_set or 'servicedetail_edit' in user_permission_set
        ):
            return
        if url_name == 'return_product_batch_add' and (
            'return_product_add' in user_permission_set or 'return_product_edit' in user_permission_set
        ):
            return
        # 3.是否具有权限（有权限)
        if _permission_candidates(url_name) & user_permission_set:
            return

        # 4.无权限
        return HttpResponse("无权访问")

#
# class UserActionLogMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         # 如果用户已登录，可以获取用户信息
#         user = getattr(request, 'user', None)
#         if user and not isinstance(user, AnonymousUser):
#             models.UserLog.objects.create(user_id=request.info_dict_useid,
#                                           action=request.path,
#                                           ip=request.META.get('REMOTE_ADDR')
#                                           )
