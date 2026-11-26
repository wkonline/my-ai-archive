from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from api.core.authentication import CoreUserJWTAuthentication
from api.core.permissions import HasPermission


class StandardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


# 表单里 remote 搜索下拉（客户、产品档案等）的最大返回条数。前端输入即查，这个值
# 只做防爆保护，不能设成 20/30 这类小值——一次拉不全，用户就会以为数据缺失。
DROPDOWN_SEARCH_LIMIT = 500


class BaseModelViewSet(ModelViewSet):
    """通用 CRUD ViewSet：默认软删除过滤，支持 permission_codes 权限校验。

    - permission_codes: 列表/读取所需权限（如 contract_list）
    - action_permission_codes: {action: codes} 覆盖具体动作权限
    """
    pagination_class = StandardPagination
    search_fields = []
    authentication_classes = [CoreUserJWTAuthentication]
    permission_classes = [HasPermission]
    permission_codes = None
    action_permission_codes = None

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.queryset.model, 'is_delete'):
            qs = qs.filter(is_delete=False)
        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError as e:
            # 硬删除遇到外键保护时必须返回 400，不能让 Django 抛 500：
            # 例如删除还有合同的客户、被产品引用的分类等。
            names = sorted({
                str(obj._meta.verbose_name) for obj in e.protected_objects})
            return Response(
                {'detail': '该记录已被{}引用，无法删除。'.format('、'.join(names))},
                status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """软删除：有 is_delete 字段则置 True，否则硬删除。

        子类覆盖时必须调用 super()，否则删除会静默失效。
        """
        if hasattr(instance, 'is_delete'):
            instance.is_delete = True
            instance.save(update_fields=['is_delete'])
            return
        instance.delete()
