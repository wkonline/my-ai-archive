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
    action_permission_codes = {'me': [], 'update_profile': []}

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


class CustomerViewSet(BaseModelViewSet):
    queryset = models.Customer.objects.select_related('saler').all()
    serializer_class = CustomerSerializer
    permission_codes = 'customer_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['company_name', 'contact_person']

    def get_queryset(self):
        qs = super().get_queryset()
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(
                Q(company_name__icontains=keyword) |
                Q(contact_person__icontains=keyword) |
                Q(saler__username__icontains=keyword))
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
        data = [{
            '客户名称': c.company_name,
            '联系人': c.contact_person or '',
            '电话': c.phone or '',
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
