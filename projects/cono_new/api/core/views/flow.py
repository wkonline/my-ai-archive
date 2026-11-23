"""售后流转（实物台账）：产品档案 / 寄给客户登记 / 客户返回登记

状态机（与前端约定一致）：
  ① 公司库存 --寄出--> ② 客户试用中 --返回--> ① 公司库存 或 ③ 维修中
  ③ 维修中 --维修完成--> ① 公司库存
换板只决定「哪块板」，送修只决定「这块板去哪」，两个判断串行不嵌套。
所有状态变更都写 FlowStatusLog。
"""
import datetime
from io import BytesIO

from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.core import models
from api.core.serializers.flow import (
    ProductArchiveSerializer, FlowOutSerializer, FlowReturnSerializer,
    SerialTransitionSerializer, FlowStatusLogSerializer,
)
from api.core.views.base import BaseModelViewSet

FLOW_NUMBER_PREFIX = 'CN'


def _current_operator(request):
    user = getattr(request, 'user', None)
    return user if user and getattr(user, 'pk', None) else None


def _write_status_log(archive, from_status, to_status, operator, remark=''):
    models.FlowStatusLog.objects.create(
        archive=archive,
        from_status=from_status,
        to_status=to_status,
        operator=operator,
        date=datetime.date.today(),
        remark=remark,
    )


def _build_flow_number(day):
    """CN + 年 + LZ + 月日 + 两位当日流水，如 CN2026LZ112301

    不能用 Max(flow_number) 取最大流水：流水过 99 后 '100' < '99'，
    字符串比较会退回旧号，所以逐个探测第一个空号。
    """
    prefix = '{}{}LZ{:02d}{:02d}'.format(FLOW_NUMBER_PREFIX, day.year, day.month, day.day)
    seq = 1
    while models.FlowOut.objects.filter(
            flow_number='{}{:02d}'.format(prefix, seq)).exists():
        seq += 1
    return '{}{:02d}'.format(prefix, seq)


class ProductArchiveViewSet(BaseModelViewSet):
    """产品档案：不提供删除，只提供停用，否则会断掉流转历史。"""
    queryset = models.ProductArchive.objects.select_related(
        'productcategory', 'product', 'handler', 'customer', 'superseded_by').all()
    serializer_class = ProductArchiveSerializer
    permission_codes = 'flow_archive_list'
    action_permission_codes = {
        'export': 'flow_archive_download_excel',
        'stock': 'flow_archive_stock',
        'toggle_active': 'flow_archive_edit',
    }
    filter_backends = [filters.SearchFilter]
    search_fields = ['serial_number']

    def get_queryset(self):
        qs = super().get_queryset()
        serial = self.request.query_params.get('serial_number')
        if serial:
            qs = qs.filter(serial_number__icontains=serial.strip())
        product_model = self.request.query_params.get('product_model')
        if product_model:
            qs = qs.filter(product__model__icontains=product_model.strip())
        customer_name = self.request.query_params.get('customer_name')
        if customer_name:
            qs = qs.filter(customer__company_name__icontains=customer_name.strip())
        status_value = self.request.query_params.get('status')
        if status_value:
            qs = qs.filter(status=status_value)
        if self.request.query_params.get('include_inactive') not in ('1', 'true'):
            qs = qs.filter(is_active=True)
        return qs.order_by('-id')

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': '产品档案不支持删除，请使用停用'}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        archive = serializer.save()
        operator = _current_operator(self.request) or archive.handler
        _write_status_log(archive, None, archive.status, operator, '新建档案')

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        archive = serializer.save()
        if old_status != archive.status:
            operator = _current_operator(self.request) or archive.handler
            _write_status_log(archive, old_status, archive.status, operator, '编辑档案')

    @action(detail=True, methods=['post'], url_path='stock')
    def stock(self, request, pk=None):
        """维修完成：③ 维修中 -> ① 公司库存"""
        archive = self.get_object()
        if archive.status != 3:
            return Response({'detail': '只有「维修中」的档案才能标记维修完成'}, status=400)
        operator = _current_operator(request) or archive.handler
        archive.status = 1
        archive.location_type = 1
        archive.customer = None
        archive.save(update_fields=['status', 'location_type', 'customer'])
        _write_status_log(archive, 3, 1, operator, '维修完成')
        return Response(ProductArchiveSerializer(archive).data)

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        archive = self.get_object()
        if archive.is_active and archive.status == 2:
            return Response({'detail': '档案在客户处，不能停用'}, status=400)
        archive.is_active = not archive.is_active
        archive.save(update_fields=['is_active'])
        return Response(ProductArchiveSerializer(archive).data)

    @action(detail=True, methods=['get'], url_path='logs')
    def logs(self, request, pk=None):
        archive = self.get_object()
        logs = archive.status_logs.select_related('operator').order_by('-id')
        return Response(FlowStatusLogSerializer(logs, many=True).data)

    @action(detail=True, methods=['get'], url_path='transitions')
    def transitions(self, request, pk=None):
        archive = self.get_object()
        rows = models.SerialTransition.objects.select_related(
            'old_archive', 'new_archive', 'operator').filter(
            Q(old_archive=archive) | Q(new_archive=archive)).order_by('-id')
        return Response(SerialTransitionSerializer(rows, many=True).data)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        import pandas as pd
        qs = self.filter_queryset(self.get_queryset())
        data = [{
            '产品序列号': a.serial_number,
            '产品名称': a.productcategory.name if a.productcategory else '',
            '产品型号': a.product.model if a.product else '',
            '经手人': a.handler.username if a.handler else '',
            '入库日期': a.stock_date,
            '当前状态': a.get_status_display(),
            '所在位置': a.customer.company_name if a.customer else a.get_location_type_display(),
            '是否已换板': '是' if a.is_superseded else '否',
            '是否启用': '是' if a.is_active else '否',
        } for a in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'product_archive_{}.xlsx'.format(
            datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

    @action(detail=False, methods=['get'], url_path='available')
    def available(self, request):
        """寄出登记用的档案下拉：只列公司库存、未换板、启用的档案。"""
        qs = models.ProductArchive.objects.select_related('product', 'productcategory').filter(
            is_delete=False, is_active=True, is_superseded=False, status=1)
        keyword = (request.query_params.get('q') or '').strip()
        if keyword:
            qs = qs.filter(Q(serial_number__icontains=keyword) |
                           Q(product__model__icontains=keyword))
        qs = qs.order_by('serial_number')[:30]
        return Response([{
            'id': a.id,
            'serial_number': a.serial_number,
            'product_model': a.product.model if a.product else '',
            'productcategory_name': a.productcategory.name if a.productcategory else '',
        } for a in qs])


class FlowOutViewSet(BaseModelViewSet):
    """寄给客户登记"""
    queryset = models.FlowOut.objects.select_related(
        'archive', 'archive__product', 'archive__productcategory', 'customer').all()
    serializer_class = FlowOutSerializer
    permission_codes = 'flow_out_list'
    action_permission_codes = {
        'export': 'flow_out_download_excel',
        'next_number': 'flow_out_add',
        'pending': 'flow_return_add',
    }
    filter_backends = [filters.SearchFilter]
    search_fields = ['flow_number', 'archive__serial_number', 'customer__company_name']

    def get_queryset(self):
        qs = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            qs = qs.filter(ship_date__range=(start_date, end_date))
        customer_name = self.request.query_params.get('customer_name')
        if customer_name:
            qs = qs.filter(customer__company_name__icontains=customer_name.strip())
        flow_number = self.request.query_params.get('flow_number')
        if flow_number:
            qs = qs.filter(flow_number__icontains=flow_number.strip())
        status_value = self.request.query_params.get('status')
        if status_value:
            qs = qs.filter(status=status_value)
        return qs.order_by('-id')

    @action(detail=False, methods=['get'], url_path='next-number')
    def next_number(self, request):
        day = datetime.date.today()
        ship_date = request.query_params.get('ship_date')
        if ship_date:
            try:
                day = datetime.date.fromisoformat(ship_date)
            except ValueError:
                pass
        return Response({'flow_number': _build_flow_number(day)})

    @transaction.atomic
    def perform_create(self, serializer):
        flow = serializer.save()
        archive = flow.archive
        from_status = archive.status
        archive.status = 2
        archive.location_type = 2
        archive.customer = flow.customer
        archive.save(update_fields=['status', 'location_type', 'customer'])
        operator = _current_operator(self.request) or archive.handler
        _write_status_log(archive, from_status, 2, operator,
                          '寄给客户：{}'.format(flow.flow_number))

    def perform_update(self, serializer):
        # 已返回的单据不允许改寄出信息，否则快照与返回记录会对不上
        instance = serializer.instance
        if instance.status != 1:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': '已返回的寄出单不能修改'})
        serializer.save()

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """删除寄出单必须回滚档案状态，否则档案会挂在客户处但单据消失。

        基类 BaseModelViewSet.destroy 直接置 is_delete，不会走到 perform_destroy，
        所以这里整体覆盖，不能只写 perform_destroy。
        """
        instance = self.get_object()
        if instance.status != 1:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': '已返回的寄出单不能删除'})
        archive = instance.archive
        from_status = archive.status
        archive.status = 1
        archive.location_type = 1
        archive.customer = None
        archive.save(update_fields=['status', 'location_type', 'customer'])
        operator = _current_operator(self.request) or archive.handler
        _write_status_log(archive, from_status, 1, operator,
                          '删除寄出单：{}'.format(instance.flow_number))
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        import pandas as pd
        qs = self.filter_queryset(self.get_queryset())
        data = [{
            '流转编号': f.flow_number,
            '产品序列号': f.archive.serial_number if f.archive else '',
            '产品型号': f.archive.product.model if f.archive and f.archive.product else '',
            '客户名称': f.customer.company_name if f.customer else '',
            '客户地址': f.customer_address or '',
            '联系人': f.contact_name or '',
            '联系电话': f.contact_phone or '',
            '寄出日期': f.ship_date,
            '快递公司': f.express_company or '',
            '快递单号': f.express_number or '',
            '预计返回日期': f.expected_return_date or '',
            '流转状态': f.get_status_display(),
        } for f in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'flow_out_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """返回登记用：只列「在客户处」的寄出单。"""
        qs = models.FlowOut.objects.select_related(
            'archive', 'archive__product', 'customer').filter(
            is_delete=False, status=1)
        keyword = (request.query_params.get('q') or '').strip()
        if keyword:
            qs = qs.filter(Q(flow_number__icontains=keyword) |
                           Q(archive__serial_number__icontains=keyword) |
                           Q(customer__company_name__icontains=keyword))
        qs = qs.order_by('-id')[:30]
        return Response([{
            'id': f.id,
            'flow_number': f.flow_number,
            'customer_name': f.customer.company_name if f.customer else '',
            'archive_id': f.archive_id,
            'serial_number': f.archive.serial_number if f.archive else '',
            'product_model': f.archive.product.model if f.archive and f.archive.product else '',
            'productcategory_name': (f.archive.productcategory.name
                                     if f.archive and f.archive.productcategory else ''),
            'ship_date': f.ship_date,
            'express_number': f.express_number or '',
        } for f in qs])


class FlowReturnViewSet(BaseModelViewSet):
    """客户返回登记：换板建档 + 送修判定"""
    queryset = models.FlowReturn.objects.select_related(
        'flow_out', 'flow_out__customer', 'flow_out__archive',
        'flow_out__archive__product', 'new_archive').all()
    serializer_class = FlowReturnSerializer
    permission_codes = 'flow_return_list'
    action_permission_codes = {
        'export': 'flow_return_download_excel',
    }
    filter_backends = [filters.SearchFilter]
    search_fields = ['flow_out__flow_number', 'snapshot_serial']

    def get_queryset(self):
        qs = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            qs = qs.filter(actual_return_date__range=(start_date, end_date))
        customer_name = self.request.query_params.get('customer_name')
        if customer_name:
            qs = qs.filter(flow_out__customer__company_name__icontains=customer_name.strip())
        flow_number = self.request.query_params.get('flow_number')
        if flow_number:
            qs = qs.filter(flow_out__flow_number__icontains=flow_number.strip())
        return qs.order_by('-id')

    def _create_new_archive(self, request, data, flow):
        """换板：用前端传来的新档案信息建档案，并返回实例。"""
        serial = (data.get('new_serial_number') or '').strip()
        if not serial:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'new_serial_number': '换板时必须填写新序列号'})
        old_archive = flow.archive
        if serial == old_archive.serial_number:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'new_serial_number': '新序列号不能与原序列号相同'})
        if models.ProductArchive.objects.filter(serial_number=serial).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'new_serial_number': '该产品序列号已存在'})

        operator = _current_operator(request) or old_archive.handler
        archive = models.ProductArchive.objects.create(
            productcategory_id=data.get('new_productcategory') or old_archive.productcategory_id,
            product_id=data.get('new_product') or old_archive.product_id,
            serial_number=serial,
            handler_id=data.get('new_handler') or operator.pk,
            stock_date=data.get('actual_return_date') or datetime.date.today(),
            status=1,
            location_type=1,
        )
        _write_status_log(archive, None, 1, operator,
                          '换板建档，原序列号 {}'.format(old_archive.serial_number))
        return archive

    @transaction.atomic
    def perform_create(self, serializer):
        request = self.request
        data = request.data
        flow = serializer.validated_data['flow_out']
        swapped = serializer.validated_data.get('is_board_swapped', False)
        result_status = serializer.validated_data.get('result_status', 1)

        new_archive = None
        if swapped:
            new_archive = self._create_new_archive(request, data, flow)

        snapshot_serial = flow.archive.serial_number
        snapshot_model = flow.archive.product.model if flow.archive.product else ''
        ret = serializer.save(
            snapshot_serial=snapshot_serial,
            snapshot_model=snapshot_model,
            new_archive=new_archive,
        )

        operator = _current_operator(request) or flow.archive.handler

        if swapped:
            old_archive = flow.archive
            # 旧板已经回到公司手上，必须同时解除客户绑定，否则它会一直挂在客户名下
            old_status = old_archive.status
            old_archive.is_superseded = True
            old_archive.superseded_by = new_archive
            old_archive.status = 1
            old_archive.location_type = 1
            old_archive.customer = None
            old_archive.save(update_fields=[
                'is_superseded', 'superseded_by', 'status', 'location_type', 'customer'])
            _write_status_log(old_archive, old_status, 1, operator,
                              '换板退役，由 {} 接替'.format(new_archive.serial_number))
            models.SerialTransition.objects.create(
                old_archive=old_archive,
                new_archive=new_archive,
                old_serial=old_archive.serial_number,
                new_serial=new_archive.serial_number,
                flow_return=ret,
                operator=operator,
                date=ret.actual_return_date,
            )
            target = new_archive
            remark = '换板返回，新序列号 {}'.format(new_archive.serial_number)
        else:
            target = flow.archive
            remark = '原板返回'

        # 送修判定作用于「最终那块板」，原板与换板走同一套流程
        from_status = target.status
        target.status = 3 if result_status == 2 else 1
        target.location_type = 1
        target.customer = None
        target.save(update_fields=['status', 'location_type', 'customer'])
        _write_status_log(target, from_status, target.status, operator,
                          '{}：{}'.format(remark, flow.flow_number))

        flow.status = 2
        flow.save(update_fields=['status'])

    def update(self, request, *args, **kwargs):
        # 返回登记一旦落库就是历史事实（含换板建档、序列号转换），改动会破坏整条追溯链
        return Response({'detail': '返回登记不支持修改，如需更正请删除后重新登记'},
                        status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """删除返回登记要把整条链回滚：寄出单回到在客户处、档案回到客户处状态。"""
        from rest_framework.exceptions import ValidationError
        instance = self.get_object()
        flow = instance.flow_out
        operator = _current_operator(self.request)
        if operator is None:
            operator = (instance.new_archive.handler if instance.new_archive
                        else flow.archive.handler)

        if instance.is_board_swapped and instance.new_archive:
            new_archive = instance.new_archive
            # 新档案如果已经被后续流转用过，就不能再撤销换板
            if models.FlowOut.objects.filter(
                    archive=new_archive, is_delete=False).exclude(pk=flow.pk).exists():
                raise ValidationError({'detail': '换板后的新档案已参与后续流转，无法撤销该返回登记'})
            old_archive = flow.archive
            old_archive.is_superseded = False
            old_archive.superseded_by = None
            old_archive.status = 2
            old_archive.location_type = 2
            old_archive.customer = flow.customer
            old_archive.save(update_fields=[
                'is_superseded', 'superseded_by', 'status', 'location_type', 'customer'])
            _write_status_log(old_archive, 1, 2, operator,
                              '撤销换板返回，恢复在客户处：{}'.format(flow.flow_number))
            models.SerialTransition.objects.filter(flow_return=instance).update(is_delete=True)
            new_archive.is_delete = True
            new_archive.save(update_fields=['is_delete'])
        else:
            archive = flow.archive
            from_status = archive.status
            archive.status = 2
            archive.location_type = 2
            archive.customer = flow.customer
            archive.save(update_fields=['status', 'location_type', 'customer'])
            _write_status_log(archive, from_status, 2, operator,
                              '撤销返回登记：{}'.format(flow.flow_number))

        flow.status = 1
        flow.save(update_fields=['status'])
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        import pandas as pd
        qs = self.filter_queryset(self.get_queryset())
        data = [{
            '流转编号': r.flow_out.flow_number if r.flow_out else '',
            '返回时序列号': r.snapshot_serial,
            '返回时型号': r.snapshot_model or '',
            '客户名称': r.flow_out.customer.company_name if r.flow_out and r.flow_out.customer else '',
            '寄出日期': r.flow_out.ship_date if r.flow_out else '',
            '实际返回日期': r.actual_return_date,
            '是否换板': '是' if r.is_board_swapped else '否',
            '新序列号': r.new_archive.serial_number if r.new_archive else '',
            '返回后状态': r.get_result_status_display(),
        } for r in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'flow_return_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response
