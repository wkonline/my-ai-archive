from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from core.permissions import HasPermission


class StandardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class BaseModelViewSet(ModelViewSet):
    """通用 CRUD ViewSet：默认软删除过滤，支持 permission_codes 权限校验。

    - permission_codes: 列表/读取所需权限（如 contract_list）
    - action_permission_codes: {action: codes} 覆盖具体动作权限
    """
    pagination_class = StandardPagination
    search_fields = []
    permission_classes = [HasPermission]
    permission_codes = None
    action_permission_codes = None

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.queryset.model, 'is_delete'):
            qs = qs.filter(is_delete=False)
        return qs

    def destroy(self, request, *args, **kwargs):
        """软删除：如果模型有 is_delete 字段则置 True，否则硬删除"""
        instance = self.get_object()
        if hasattr(instance, 'is_delete'):
            instance.is_delete = True
            instance.save(update_fields=['is_delete'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        return super().destroy(request, *args, **kwargs)
