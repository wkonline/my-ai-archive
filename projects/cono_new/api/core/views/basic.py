"""基础资料模块：部门/用户/客户/仓库/产品分类/产品"""
import datetime
from io import BytesIO
from django.http import HttpResponse
from django.db.models import Q, Sum, Count
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from api.core import models
from api.core.serializers.common import (
    DepartmentSerializer, UserSerializer, CustomerSerializer,
    WarehouseSerializer, ProductCategorySerializer, ProductSerializer,
)
from api.core.views.base import BaseModelViewSet
from api.core.permissions import permission_catalog
from cono.tools.auth_profile import canonical_menus


class DepartmentViewSet(BaseModelViewSet):
    queryset = models.Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_codes = 'department_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']


class UserViewSet(BaseModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = UserSerializer
    permission_codes = 'user_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'phone']
    # 个人中心接口是“本人操作”，不应要求 user_list 权限
    action_permission_codes = {
        'me': [], 'update_profile': [],
        'permission': ['auth_user_permission'],
    }

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """当前登录用户资料（个人中心 / 修改资料页）"""
        return Response(self.get_serializer(request.user).data)

    @action(detail=False, methods=['post'], url_path='profile')
    def update_profile(self, request):
        """修改个人资料：只允许改本人可编辑的字段"""
        allowed = {'phone', 'id_number', 'address', 'gender', 'department'}
        data = {k: v for k, v in request.data.items() if k in allowed}
        serializer = self.get_serializer(request.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.get_serializer(request.user).data)

    @action(detail=True, methods=['get', 'post'], url_path='permission')
    def permission(self, request, pk=None):
        """单个用户的权限配置（对应老版 /auth/user/<id>/permission/）。

        权限模型是「角色权限 + 个人额外允许 - 个人禁止」，
        所以这里保存的是相对角色的差异，而不是完整权限清单。
        """
        user = self.get_object()
        if request.method == 'POST':
            return self._save_permission(request, user)
        return Response(self._permission_payload(user))

    def _permission_payload(self, user):
        profile = models.AuthUserProfile.objects.filter(user=user).first()
        groups, menu_groups = permission_catalog()
        return {
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'role_display': user.role_display,
            },
            'roles': [
                {'key': r.key, 'name': r.name}
                for r in models.AuthRole.objects.all().order_by('id')
            ],
            'permission_groups': groups,
            'menu_groups': menu_groups,
            'extra_permissions': list(profile.extra_permissions or []) if profile else [],
            'denied_permissions': list(profile.denied_permissions or []) if profile else [],
            'menus': [m.get('title') for m in (profile.menus or []) if m.get('title')] if profile else [],
            'menu_customize': bool(profile.menu_customize) if profile else False,
        }

    def _save_permission(self, request, user):
        data = request.data
        role_key = (data.get('role') or '').strip()
        if role_key:
            # 改角色等于提权，与 UserSerializer 保持一致只允许管理员操作
            if getattr(request.user, 'role', '') != 'admin':
                return Response({'detail': '只有管理员可以修改用户角色'}, status=403)
            if not models.AuthRole.objects.filter(key=role_key).exists():
                return Response({'role': '角色不存在'}, status=400)
            if user.role != role_key:
                user.role = role_key
                user.save(update_fields=['role'])

        groups, _ = permission_catalog()
        known = {item['code'] for g in groups for item in g['items']}
        extra = [c for c in (data.get('extra_permissions') or []) if c in known]
        denied = [c for c in (data.get('denied_permissions') or []) if c in known]
        # 同一权限既允许又禁止时以禁止为准，避免两条规则打架
        denied_set = set(denied)
        extra = [c for c in extra if c not in denied_set]

        menu_map = {item['title']: item for item in canonical_menus()}
        menus = [menu_map[t] for t in (data.get('menus') or []) if t in menu_map]

        profile, _ = models.AuthUserProfile.objects.get_or_create(user=user)
        profile.extra_permissions = sorted(set(extra))
        profile.denied_permissions = sorted(denied_set)
        profile.menus = menus
        profile.menu_customize = bool(data.get('menu_customize'))
        profile.save()
        return Response(self._permission_payload(user))


class CustomerViewSet(BaseModelViewSet):
    queryset = models.Customer.objects.select_related('saler').prefetch_related('contacts').all()
    serializer_class = CustomerSerializer
    permission_codes = 'customer_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['company_name', 'contact_person', 'contacts__name', 'contacts__phone']

    def get_queryset(self):
        qs = super().get_queryset()
        keyword = self.request.query_params.get('keyword')
        if keyword:
            # 联系人子表联查会放大结果集，必须去重
            qs = qs.filter(
                Q(company_name__icontains=keyword) |
                Q(contact_person__icontains=keyword) |
                Q(contacts__name__icontains=keyword) |
                Q(contacts__phone__icontains=keyword) |
                Q(saler__username__icontains=keyword)).distinct()
        return qs.order_by('company_name')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        by_saler = {}
        for c in qs:
            name = c.saler.username if c.saler else 'unknown'
            by_saler[name] = by_saler.get(name, 0) + 1
        return Response({'total': qs.count(), 'by_saler': by_saler})

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """客户数据导出"""
        import pandas as pd
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)

        def all_contacts(customer):
            return '；'.join(
                '{}{}'.format(ct.name, ' ' + ct.phone if ct.phone else '')
                for ct in customer.contacts.all())

        data = [{
            '客户名称': c.company_name,
            '联系人': c.contact_person or '',
            '电话': c.phone or '',
            '全部联系人': all_contacts(c),
            '地址': c.address or '',
            '业务员': c.saler.username if c.saler else '',
        } for c in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'customer_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response


class WarehouseViewSet(BaseModelViewSet):
    queryset = models.Warehouse.objects.order_by('id')
    serializer_class = WarehouseSerializer
    permission_codes = 'warehouse_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ProductCategoryViewSet(BaseModelViewSet):
    queryset = models.ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_codes = 'productcategory_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        qs = super().get_queryset()
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(name__icontains=keyword)
        return qs.order_by('name')

    @action(detail=False, methods=['post'], url_path='batch')
    def batch_upload(self, request):
        """批量上传产品分类（Excel）"""
        import pandas as pd
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'detail': '请选择文件'}, status=400)
        try:
            df = pd.read_excel(uploaded_file)
        except Exception as e:
            return Response({'detail': '文件解析失败: {}'.format(e)}, status=400)
        created = 0
        skipped = 0
        for _, row in df.iterrows():
            name = str(row.get('产品名称', '')).strip() if '产品名称' in row else str(row.get('name', '')).strip()
            if not name:
                continue
            if models.ProductCategory.objects.filter(name=name).exists():
                skipped += 1
                continue
            description = ''
            if '产品描述' in row:
                description = str(row.get('产品描述', ''))
            elif 'description' in row:
                description = str(row.get('description', ''))
            models.ProductCategory.objects.create(name=name, description=description or None)
            created += 1
        return Response({'created': created, 'skipped': skipped})

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        import pandas as pd
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        data = [{'产品名称': c.name, '产品描述': c.description or ''} for c in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'productcategory_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response


class ProductViewSet(BaseModelViewSet):
    queryset = models.Product.objects.select_related('productcategory', 'warehouse').all()
    serializer_class = ProductSerializer
    permission_codes = 'product_list'
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['productcategory', 'warehouse']
    search_fields = ['model', 'productcategory__name']

    def get_queryset(self):
        qs = super().get_queryset()
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(
                Q(model__icontains=keyword) |
                Q(productcategory__name__icontains=keyword) |
                Q(description__icontains=keyword))
        return qs.order_by('model')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        by_cat = {}
        for p in qs:
            name = p.productcategory.name if p.productcategory else 'unknown'
            by_cat[name] = by_cat.get(name, 0) + 1
        return Response({
            'total': qs.count(),
            'by_category': by_cat,
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """产品数据导出"""
        import pandas as pd
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        data = [{
            '产品名称': p.productcategory.name if p.productcategory else '',
            '产品型号': p.model,
            '仓库': p.warehouse.name if p.warehouse else '',
            '产品描述': p.description or '',
        } for p in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'product_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response
