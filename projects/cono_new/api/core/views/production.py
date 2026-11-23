"""生产模块：生产计划/派任务单/资料上传/产品铭牌/发货信息"""
import datetime
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from io import BytesIO
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from api.core import models
from api.core.serializers.common import (
    PlanSerializer, ProductionTaskSerializer,
    ContractFileSerializer, ProductLabelSerializer, ProductDeliverySerializer,
)
from api.core.views.base import BaseModelViewSet


class PlanViewSet(BaseModelViewSet):
    queryset = models.Plan.objects.select_related(
        'contract', 'contract__customer', 'productcategory', 'product', 'production_man').all()
    serializer_class = PlanSerializer
    permission_codes = 'plan_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['contract__contract_number', 'product__model', 'productcategory__name', 'contract_reserve']

    def get_queryset(self):
        qs = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            qs = qs.filter(effective_date__range=(start_date, end_date))
        contract = self.request.query_params.get('contract_number')
        if contract:
            qs = qs.filter(
                Q(contract__contract_number__icontains=contract.strip()) |
                Q(contract_reserve__icontains=contract.strip()))
        completed = self.request.query_params.get('completed')
        if completed:
            qs = qs.filter(completed=(completed == 'True'))
        # 生产状态筛选：待生产(1)、生产中(2)、已完成(3)
        production_status = self.request.query_params.get('completed_status')
        if production_status:
            try:
                qs = qs.filter(completed_status=int(production_status))
            except (ValueError, TypeError):
                pass
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(
                Q(product__model__icontains=keyword.strip()) |
                Q(productcategory__name__icontains=keyword.strip()) |
                Q(contract__contract_number__icontains=keyword.strip()))
        # 默认按新增时间倒序，前端可通过 ?ordering= 覆盖
        ordering = self.request.query_params.get('ordering', '-id')
        return qs.order_by(ordering)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        data = qs.aggregate(
            total_qty=Sum('quantity'),
            in_production=Count('id', filter=Q(completed_status=2)),
            completed=Count('id', filter=Q(completed_status=3)),
            pending=Count('id', filter=Q(completed_status=1)),
        )
        return Response({
            'total_qty': data['total_qty'] or 0,
            'in_production': data['in_production'] or 0,
            'completed': data['completed'] or 0,
            'pending': data['pending'] or 0,
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """生产计划数据导出 Excel（与原版 plan_download_excel 一致）"""
        import pandas as pd
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        data = [{
            '合同编号': item.contract.contract_number,
            '产品名称': item.productcategory.name if item.productcategory else '',
            '产品型号': item.product.model if item.product else '',
            '数量': item.quantity,
            '配置': item.configuration,
            '单位': item.get_unit_display(),
            '生效日期': item.effective_date,
            '交货日期': item.delivery_date,
        } for item in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'plan_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response


class ProductionTaskViewSet(BaseModelViewSet):
    queryset = models.ProductionTask.objects.select_related(
        'contract', 'contract__contract', 'contract__contract__customer', 'production_man').all()
    serializer_class = ProductionTaskSerializer
    permission_codes = 'task_list'

    def get_queryset(self):
        qs = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            qs = qs.filter(date__range=(start_date, end_date))
        contract_number = self.request.query_params.get('contract_number')
        if contract_number:
            qs = qs.filter(
                Q(contract__contract__contract_number__icontains=contract_number.strip()) |
                Q(contract__contract_reserve__icontains=contract_number.strip()))
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(
                Q(productcategory__icontains=keyword.strip()) |
                Q(product__icontains=keyword.strip()))
        return qs.order_by('-date')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        data = qs.aggregate(total_qty=Sum('quantity'), task_count=Count('id'))
        by_man = {}
        for t in qs.select_related('production_man'):
            name = t.production_man.username if t.production_man else 'unknown'
            by_man[name] = by_man.get(name, 0) + (t.quantity or 0)
        return Response({
            'task_count': data['task_count'],
            'total_qty': data['total_qty'] or 0,
            'by_manufacturer': by_man,
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """派任务单数据导出"""
        import pandas as pd
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        data = []
        for t in qs:
            plan = t.contract
            contract = plan.contract
            data.append({
                '项目编号': '' if plan.is_temp_plan else contract.contract_number,
                '客户名称': contract.customer.company_name if contract.customer else '',
                '产品名称': t.productcategory or '',
                '产品型号': t.product or '',
                '计划数量': plan.quantity,
                '下单数量': t.quantity,
                '下发日期': t.date,
                '负责人': t.production_man.username if t.production_man else '',
            })
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'task_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

    filter_backends = [filters.SearchFilter]
    search_fields = ['contract__contract_number', 'product']


class ContractFileViewSet(BaseModelViewSet):
    queryset = models.ContractFile.objects.select_related(
        'contract', 'contract__productcategory', 'contract__product').all()
    serializer_class = ContractFileSerializer
    permission_codes = 'contract_file_list'
    action_permission_codes = {
        'create': ['contract_file', 'contract_file_list'],
        'update': ['edit_contract_file'],
        'partial_update': ['edit_contract_file'],
        'destroy': ['delete_contract_file'],
    }

    def get_queryset(self):
        qs = super().get_queryset()
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(
                Q(contract__contract__contract_number__icontains=keyword) |
                Q(contract__contract_reserve__icontains=keyword) |
                Q(contract__product__model__icontains=keyword))
        return qs.order_by('-id')

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """上传项目文件（电气图/说明书/其他/机械图/装箱清单）"""
        contract_id = request.data.get('contract')
        field = request.data.get('field')
        f = request.FILES.get('file')
        if not contract_id or not field or not f:
            return Response({'detail': '请选择项目编号、文件类型和文件'}, status=400)
        valid_fields = ['electrical_drawings', 'instruction', 'packing_list', 'mechanical_drawings', 'other_file']
        if field not in valid_fields:
            return Response({'detail': '无效的文件类型'}, status=400)
        obj = models.ContractFile.objects.filter(contract_id=contract_id, is_delete=False).first()
        if obj is None:
            obj = models.ContractFile(contract_id=contract_id)
        setattr(obj, field, f)
        obj.save()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class ProductLabelViewSet(BaseModelViewSet):
    queryset = models.ProductLabel.objects.select_related(
        'product', 'product__productcategory').all()
    serializer_class = ProductLabelSerializer
    permission_codes = 'productlabel_list'

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(product__model__icontains=q.strip())
        return qs.order_by('id')

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """产品铭牌数据导出"""
        import pandas as pd
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        data = [{
            '产品名称': item.product.productcategory.name if item.product.productcategory else '',
            '产品型号': item.product.model,
            '电源功率(kW)': item.power,
            '电源频率(kHz)': item.frequency,
            '供电容量(kVA)': item.sup_capacity,
            '供电电压(V)': item.sup_voltage,
            '供电频率(Hz)': item.sup_frequency,
            '供电电流(A)': item.sup_current,
            '最高进水温度(°C)': item.max_in_temp,
            '最大压力(MPa)': item.max_pressure,
            '最小流量(L/min)': item.min_flow,
            '最小压力(MPa)': item.min_pressure,
        } for item in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'productlabel_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

    filter_backends = [filters.SearchFilter]
    search_fields = ['product__model']


class ProductDeliveryViewSet(BaseModelViewSet):
    queryset = models.ProductDelivery.objects.select_related(
        'customer', 'contract', 'contract__contract', 'contract__productcategory',
        'contract__product', 'delivery_man').all()
    serializer_class = ProductDeliverySerializer
    permission_codes = 'delivery_list'

    def get_queryset(self):
        qs = super().get_queryset()
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            qs = qs.filter(contract__contract_id=contract_id)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            qs = qs.filter(date__range=(start_date, end_date))
        customer_name = self.request.query_params.get('customer_name')
        if customer_name:
            qs = qs.filter(customer__company_name__icontains=customer_name.strip())
        return qs.order_by('-date')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """本年度分月发货数量 + 本年发货汇总"""
        today = datetime.date.today()
        months = []
        values = []
        for month in range(1, 13):
            month_start = datetime.date(today.year, month, 1)
            month_end = (datetime.date(today.year + 1, 1, 1)
                         if month == 12 else datetime.date(today.year, month + 1, 1))
            total = models.ProductDelivery.objects.filter(
                is_delete=False, date__gte=month_start, date__lt=month_end,
            ).aggregate(total=Sum('quantity'))['total'] or 0
            months.append('{}月'.format(month))
            values.append(int(total))
        qs = self.get_queryset()
        data = qs.aggregate(total_qty=Sum('quantity'), delivery_count=Count('id'))
        return Response({
            'months': months,
            'values': values,
            'chart_total': sum(values),
            'delivery_count': data['delivery_count'] or 0,
            'total_qty': data['total_qty'] or 0,
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """发货信息导出"""
        import pandas as pd
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        data = []
        for d in qs:
            data.append({
                '客户名称': d.customer.company_name if d.customer else '',
                '发货日期': d.date,
                '项目编号': d.contract.contract.contract_number if d.contract and d.contract.contract else (d.contract.contract_reserve or ''),
                '产品名称': d.productcategory or '',
                '产品型号': d.product or '',
                '数量': d.quantity,
                '收货人': d.customer.contact_person if d.customer else '',
                '收货人联系电话': d.customer.phone if d.customer else '',
                '收货地址': d.customer.address if d.customer else '',
                '发货人': d.delivery_man.username if d.delivery_man else '',
            })
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'delivery_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

    filter_backends = [filters.SearchFilter]
    search_fields = ['customer__company_name']
