"""生产模块：生产计划/派任务单/资料上传/产品铭牌/发货信息"""
import datetime
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from io import BytesIO
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from api.core import models
from api.core.serializers.common import (
    PlanSerializer, ProductionTaskSerializer,
    ContractFileSerializer, ProductLabelSerializer, ProductDeliverySerializer,
)
from api.core.views.base import BaseModelViewSet
from cono.tools.helper import save_receiver_as_contact


def _delivered_quantity(plan):
    return models.ProductDelivery.objects.filter(
        contract=plan, is_delete=False,
    ).aggregate(total=Sum('quantity'))['total'] or 0


def _parse_year(raw, today=None):
    """解析统计年份，非法或缺失时回落到当前年份。"""
    today = today or datetime.date.today()
    try:
        year = int(raw)
    except (TypeError, ValueError):
        return today.year
    return year if 1970 <= year <= 2999 else today.year


def _derive_plan_status(plan):
    """按发货量与任务单推导计划应处的 (completed_status, completed)。

    只依据现存记录判断，无任何生产记录时返回 None 表示「无从判断」，
    由各调用方按自己的业务约定决定，避免把不同场景揉进一条规则：
    - 发货量达到计划量：已完成(3)
    - 有发货或有任务单：生产中(2)
    """
    delivered = _delivered_quantity(plan)
    if plan.quantity and delivered >= plan.quantity:
        return 3, True
    if delivered > 0:
        return 2, False
    if models.ProductionTask.objects.filter(
            contract=plan, is_delete=False).exists():
        return 2, False
    return None


def _apply_plan_status(plan, status, completed):
    if (plan.completed_status, plan.completed) != (status, completed):
        plan.completed_status = status
        plan.completed = completed
        plan.save(update_fields=['completed_status', 'completed', 'update_time'])


def _refresh_plan_delivery_status(plan):
    """发货增删后刷新状态，与老系统 cono/views/delivery.py 保持一致。

    发满计划量即已完成，否则回到生产中。发货记录被删除不代表生产没开始过，
    所以无记录时也保持生产中，不能退回待生产。
    """
    if plan is None:
        return
    _apply_plan_status(plan, *(_derive_plan_status(plan) or (2, False)))


def _refresh_plan_task_status(plan):
    """派单/改单/删单后刷新生产状态。

    已完成的计划不回退：发货完结的记录不应因为删任务单被改回生产中。
    任务单和发货都清空时退回待生产，与老系统派单逻辑一致。
    """
    if plan is None or plan.completed_status == 3:
        return
    _apply_plan_status(plan, *(_derive_plan_status(plan) or (1, False)))


def _truthy(value):
    """前端可能传 true/'true'/'1'/1，统一归一化。"""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def _is_plan_completed(status):
    """completed_status 为 3（已完成）时，冗余的 completed 布尔值才为 True。"""
    return status == 3


class PlanViewSet(BaseModelViewSet):
    queryset = models.Plan.objects.select_related(
        'contract', 'contract__customer', 'productcategory', 'product', 'production_man').all()
    serializer_class = PlanSerializer
    permission_codes = 'plan_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['contract__contract_number', 'product__model', 'productcategory__name', 'contract_reserve']
    action_permission_codes = {
        'pending_contracts': ['plan_list', 'task_list', 'task_add'],
        'pending_products': ['plan_list', 'task_list', 'task_add'],
    }

    def perform_create(self, serializer):
        # completed 是 completed_status 的冗余布尔值，老代码多处直接读它。
        # 计划表单只提交 completed_status，不同步的话「已完成」的计划会带着
        # completed=False 入库，统计口径就分叉了。
        serializer.save(completed=_is_plan_completed(
            serializer.validated_data.get('completed_status', 1)))

    def perform_update(self, serializer):
        serializer.save(completed=_is_plan_completed(
            serializer.validated_data.get(
                'completed_status', serializer.instance.completed_status)))

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

    def _unassigned_pending_plans(self):
        """待生产且尚未派任务单的计划。

        派过任务单的计划不再出现在新派单下拉里，判断依据是老系统同一套约定：
        任务单存在即视为已派工（软删除的不算）。
        """
        assigned = models.ProductionTask.objects.filter(
            is_delete=False).values('contract_id')
        return models.Plan.objects.filter(
            completed_status=1, is_delete=False,
        ).exclude(id__in=assigned)

    @action(detail=False, methods=['get'], url_path='pending-contracts')
    def pending_contracts(self, request):
        """新派任务单的项目编号候选。

        筛选必须在服务端完成：前端原先拉 /plan/?page_size=2000 再在浏览器里
        过滤，但分页上限是 200，计划总数一超就截断，目标项目会整批消失。
        """
        qs = self._unassigned_pending_plans()
        keyword = (request.query_params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(
                Q(contract__contract_number__icontains=keyword) |
                Q(contract_reserve__icontains=keyword))

        rows = qs.values(
            'contract_id', 'contract__contract_number',
            'contract__customer__company_name', 'contract_reserve',
        ).annotate(plan_count=Count('id'))

        contracts, reserves = {}, {}
        for row in rows:
            if (row['contract__contract_number'] or '') == models.TEMP_CONTRACT_NUMBER:
                reserve = (row['contract_reserve'] or '').strip()
                if not reserve:
                    continue
                reserves[reserve] = {
                    'value': 'reserve:' + reserve,
                    'label': reserve,
                    'is_temp': True,
                    'customer_name': '',
                    'plan_count': row['plan_count'],
                }
            else:
                contracts[row['contract_id']] = {
                    'value': row['contract_id'],
                    'label': row['contract__contract_number'] or '',
                    'is_temp': False,
                    'customer_name': row['contract__customer__company_name'] or '',
                    'plan_count': row['plan_count'],
                }

        # 真实合同按编号倒序在前，临时计划（无合同）单独排在后面
        data = sorted(contracts.values(), key=lambda e: str(e['label']), reverse=True)
        data += sorted(reserves.values(), key=lambda e: str(e['label']), reverse=True)
        return Response({'results': data, 'total': len(data)})

    @action(detail=False, methods=['get'], url_path='pending-products')
    def pending_products(self, request):
        """选定项目编号后展开的可下单产品行（按计划行，一行一个产品）。"""
        qs = self._unassigned_pending_plans().select_related('productcategory', 'product')
        reserve = (request.query_params.get('reserve') or '').strip()
        if reserve:
            qs = qs.filter(contract_reserve=reserve)
        else:
            contract_id = request.query_params.get('contract')
            if not contract_id:
                return Response({'results': []})
            qs = qs.filter(contract_id=contract_id)

        return Response({'results': [{
            'plan_id': plan.id,
            'productcategory': plan.productcategory.name if plan.productcategory else '',
            'product': plan.product.model if plan.product else '',
            'plan_quantity': plan.quantity,
        } for plan in qs.order_by('id')]})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        # 四张卡片是"本年度总览"，不能跟随列表筛选：
        # 走 self.get_queryset() 会把 completed_status/日期/关键词一起带上，
        # 点"待生产"后四张卡片会同时塌缩成筛选结果，看起来像数据丢了。
        # 用 super().get_queryset() 跳过本类的请求参数过滤，只保留软删除过滤。
        qs = super().get_queryset()
        year = _parse_year(request.query_params.get('year'))
        year_start = datetime.date(year, 1, 1)
        next_year = datetime.date(year + 1, 1, 1)
        year_qs = qs.filter(effective_date__gte=year_start, effective_date__lt=next_year)
        # 四张卡片都按"电源台数"统计，统一用 Sum('quantity')。
        # 用 Count('id') 数的是计划行数，一行可能对应多台，卡片之间对不上总数。
        data = year_qs.aggregate(
            total_qty=Sum('quantity'),
            in_production=Sum('quantity', filter=Q(completed_status=2)),
            completed=Sum('quantity', filter=Q(completed_status=3)),
            pending=Sum('quantity', filter=Q(completed_status=1)),
        )
        return Response({
            'year': year,
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

    def perform_create(self, serializer):
        # 负责人由 ProductionTaskSerializer 统一取当前登录用户
        serializer.save()
        _refresh_plan_task_status(serializer.instance.contract)

    def perform_update(self, serializer):
        old_plan = serializer.instance.contract
        task = serializer.save()
        _refresh_plan_task_status(task.contract)
        # 改挂到别的计划时，原计划也要重算
        if old_plan and old_plan.pk != task.contract_id:
            _refresh_plan_task_status(old_plan)

    def perform_destroy(self, instance):
        plan = instance.contract
        super().perform_destroy(instance)
        _refresh_plan_task_status(plan)

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
    action_permission_codes = {
        'create': ['delivery_add', 'delivery_create'],
        'update': ['delivery_edit'],
        'partial_update': ['delivery_edit'],
        'destroy': ['delivery_delete'],
    }

    def perform_create(self, serializer):
        # 发货人由 ProductDeliverySerializer 统一取当前登录用户
        delivery = serializer.save()
        _refresh_plan_delivery_status(delivery.contract)

    def _check_quantity(self, plan, quantity, exclude_id=None):
        """校验本次发货数量不超过该计划的剩余量（编辑时排除自身）。"""
        qs = models.ProductDelivery.objects.filter(contract=plan, is_delete=False)
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        delivered = qs.aggregate(total=Sum('quantity'))['total'] or 0
        remaining = max(plan.quantity - delivered, 0)
        if not quantity or int(quantity) <= 0:
            raise ValidationError({'detail': '发货数量必须大于 0'})
        if int(quantity) > remaining:
            raise ValidationError({'detail': '发货数量不能大于剩余数量 {}'.format(remaining)})

    def perform_update(self, serializer):
        old_plan = serializer.instance.contract
        plan = serializer.validated_data.get('contract', old_plan)
        quantity = serializer.validated_data.get('quantity', serializer.instance.quantity)
        self._check_quantity(plan, quantity, exclude_id=serializer.instance.pk)
        save_as_contact = _truthy(self.request.data.get('save_as_contact'))
        delivery = serializer.save()
        # 改挂到别的计划时，原计划也要重算
        _refresh_plan_delivery_status(delivery.contract)
        if old_plan and old_plan.pk != delivery.contract_id:
            _refresh_plan_delivery_status(old_plan)
        if save_as_contact and delivery.receiver:
            save_receiver_as_contact(delivery.customer, delivery.receiver, delivery.receiver_phone)

    def perform_destroy(self, instance):
        plan = instance.contract
        super().perform_destroy(instance)
        _refresh_plan_delivery_status(plan)

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

    @action(detail=False, methods=['get'], url_path='contract-items')
    def contract_items(self, request):
        """按项目号（合同）返回待发货物料清单。

        一个项目号下可能有多条生产计划（每个产品一条），前端据此渲染多行；
        每行带上计划量、已发量、剩余量，避免用户超发。
        """
        contract_id = request.query_params.get('contract')
        if not contract_id:
            return Response({'detail': '请提供项目号'}, status=400)
        contract = models.Contract.objects.filter(pk=contract_id).select_related('customer').first()
        if contract is None:
            return Response({'detail': '项目号不存在'}, status=404)

        plans = models.Plan.objects.filter(
            contract=contract, is_delete=False,
        ).select_related('productcategory', 'product').order_by('id')

        # 一次聚合出所有计划的已发数量，避免逐条查询
        delivered_map = dict(
            models.ProductDelivery.objects.filter(
                contract__in=plans, is_delete=False,
            ).values_list('contract_id').annotate(total=Sum('quantity'))
        )

        items = []
        for plan in plans:
            delivered = delivered_map.get(plan.id, 0) or 0
            items.append({
                'plan': plan.id,
                'productcategory': plan.productcategory.name if plan.productcategory else '',
                'product': plan.product.model if plan.product else '',
                'unit': plan.get_unit_display(),
                'quantity': plan.quantity,
                'delivered': delivered,
                'remaining': max(plan.quantity - delivered, 0),
                'completed_status': plan.completed_status,
            })

        customer = contract.customer
        contacts = [
            {
                'name': c.name,
                'phone': c.phone or '',
                'title': c.title or '',
                'is_primary': c.is_primary,
            }
            for c in customer.contacts.all()
        ]
        return Response({
            'contract': contract.id,
            'contract_number': contract.contract_number,
            'customer': customer.id,
            'customer_name': customer.company_name,
            'contact_person': customer.contact_person or '',
            'phone': customer.phone or '',
            'address': customer.address or '',
            'contacts': contacts,
            'items': items,
        })

    @action(detail=False, methods=['post'], url_path='batch-create')
    def batch_create(self, request):
        """一次提交多行发货（同一项目号下的多个产品）。

        任一行校验失败则整批不落库，避免出现「发了一半」的单据。
        """
        customer_id = request.data.get('customer')
        contract_id = request.data.get('contract')
        date = request.data.get('date')
        rows = request.data.get('items') or []

        if not contract_id:
            return Response({'detail': '请选择项目号'}, status=400)
        if not date:
            return Response({'detail': '请选择发货日期'}, status=400)
        if not rows:
            return Response({'detail': '请至少填写一行发货产品'}, status=400)

        contract = models.Contract.objects.filter(pk=contract_id).select_related('customer').first()
        if contract is None:
            return Response({'detail': '项目号不存在'}, status=400)
        customer = models.Customer.objects.filter(pk=customer_id).first() or contract.customer

        errors = []
        prepared = []
        for index, row in enumerate(rows, start=1):
            plan_id = row.get('plan')
            plan = models.Plan.objects.filter(pk=plan_id, contract=contract).first()
            if plan is None:
                errors.append('第 {} 行：产品不存在或不属于该项目号'.format(index))
                continue
            try:
                quantity = int(row.get('quantity') or 0)
            except (TypeError, ValueError):
                quantity = 0
            if quantity <= 0:
                errors.append('第 {} 行：发货数量必须大于 0'.format(index))
                continue
            delivered = models.ProductDelivery.objects.filter(
                contract=plan, is_delete=False,
            ).aggregate(total=Sum('quantity'))['total'] or 0
            remaining = max(plan.quantity - delivered, 0)
            if quantity > remaining:
                errors.append('第 {} 行：{} {} 发货数量 {} 超出剩余数量 {}'.format(
                    index,
                    plan.productcategory.name if plan.productcategory else '',
                    plan.product.model if plan.product else '',
                    quantity, remaining))
                continue
            prepared.append((plan, quantity, row))

        if errors:
            return Response({'detail': '；'.join(errors)}, status=400)

        receiver = (request.data.get('receiver') or '').strip()
        receiver_phone = (request.data.get('receiver_phone') or '').strip()
        receiver_address = (request.data.get('receiver_address') or '').strip()
        # 收货人只落单据快照，不默认改动客户档案；用户明确勾选才回写联系人
        save_as_contact = _truthy(request.data.get('save_as_contact'))

        with transaction.atomic():
            for plan, quantity, row in prepared:
                models.ProductDelivery.objects.create(
                    customer=customer,
                    date=date,
                    contract=plan,
                    productcategory=row.get('productcategory') or (
                        plan.productcategory.name if plan.productcategory else ''),
                    product=row.get('product') or (plan.product.model if plan.product else ''),
                    quantity=quantity,
                    delivery_man=request.user,
                    receiver=receiver,
                    receiver_phone=receiver_phone,
                    receiver_address=receiver_address,
                )
                _refresh_plan_delivery_status(plan)

        if save_as_contact and receiver:
            save_receiver_as_contact(customer, receiver, receiver_phone)

        return Response({'created': len(prepared)}, status=201)


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
