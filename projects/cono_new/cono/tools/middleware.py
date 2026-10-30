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


class AuthMiddleware(MiddlewareMixin):

    def process_request(self, request):
        # 1.不用登录就可以访问处理
        if request.path_info in ["/login/", "/image/code/","/register/", "/dify/search/"]:
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
        cleanup_expired_user_logs_daily()
        models.UserLog.objects.create(user_id=request.info_dict_useid,
                                      action=request.path,
                                      ip=request.META.get('REMOTE_ADDR')
                                      )
        return

    def process_view(self, request, view_func, args, kwargs):
        if request.path_info in [
            '/login/', '/logout/', '/image/code/', '/',
            '/ajax/search-companys/', '/ajax/check-contract-number/',
            '/ajax/delivery-customer-info/', '/ajax/get-plan-contract-products/',
            '/register/', '/dify/search/',
        ]:
            return
        # 1.当前用户角色
        role = request.info_dict_role
        # 2.允许用户修改/重置自己的资料和密码
        url_name = request.resolver_match.url_name
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
        required_permission = URL_PERMISSION_ALIASES.get(url_name, url_name)
        if required_permission in user_permission_set:
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
