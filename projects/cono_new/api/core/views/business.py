"""核心业务模块：合同/回款/发票"""
import datetime
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.db.models import Q, Sum, Max, OuterRef, Subquery, Value, F
from django.db.models import DecimalField
from django.db.models.functions import Coalesce
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from api.core import models
from api.core.serializers.common import (
    ContractSerializer, ContractProductSerializer,
    CollectionSerializer, InvoiceSerializer,
)
from api.core.views.base import BaseModelViewSet


class ContractViewSet(BaseModelViewSet):
    queryset = models.Contract.objects.select_related('customer').all()
    serializer_class = ContractSerializer
    permission_codes = 'contract_list'
    action_permission_codes = {
        'create': ['contract_add', 'contract_create'],
        'update': ['contract_edit'],
        'partial_update': ['contract_edit'],
        'destroy': ['contract_delete'],
    }
    filter_backends = [filters.SearchFilter]
    search_fields = ['contract_number', 'customer__company_name']

    def get_queryset(self):
        qs = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            qs = qs.filter(date__range=(start_date, end_date))
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(
                Q(contract_number__icontains=keyword) |
                Q(customer__company_name__icontains=keyword))
        # 状态筛选：已开票欠款 / 未开票合同
        status_filter = self.request.query_params.get('status')
        if status_filter in ('invoiced_debt', 'uninvoiced'):
            money_field = DecimalField(max_digits=10, decimal_places=2)
            inv_sum = models.Invoice.objects.filter(contract=OuterRef('pk'), is_delete=False).values('contract').annotate(
                total=Sum('amount')).values('total')
            qs = qs.annotate(
                _inv_total=Coalesce(Subquery(inv_sum, output_field=money_field), Value(Decimal('0')), output_field=money_field),
            )
            if status_filter == 'invoiced_debt':
                # 已开票（开票金额>0）但款未付清（回款金额<合同金额）
                col_sum = models.Collection.objects.filter(contract=OuterRef('pk'), is_delete=False).values('contract').annotate(
                    total=Sum('amount')).values('total')
                qs = qs.annotate(
                    _col_total=Coalesce(Subquery(col_sum, output_field=money_field), Value(Decimal('0')), output_field=money_field),
                ).filter(_inv_total__gt=0, _col_total__lt=F('total_price'))
            else:
                # 未开票且未付清：开票金额为0且回款金额<合同金额
                col_sum = models.Collection.objects.filter(contract=OuterRef('pk'), is_delete=False).values('contract').annotate(
                    total=Sum('amount')).values('total')
                qs = qs.annotate(
                    _col_total=Coalesce(Subquery(col_sum, output_field=money_field), Value(Decimal('0'), output_field=money_field), output_field=money_field),
                ).filter(_inv_total=0, _col_total__lt=F('total_price'))
        return qs.order_by('-id')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        done = qs.filter(payment_completed=True).count()
        pending = qs.filter(payment_completed=False).count()
        return Response({
            'count': qs.count(),
            'total_amount': qs.aggregate(total=Sum('total_price'))['total'] or 0,
            'pending_count': pending,
            'done_count': done,
        })

    @action(detail=False, methods=['get'], url_path='ar')
    def ar(self, request):
        """应收应付：开票未付款 / 未开票未付款合同（参考老程序 chart_list，改用 Subquery 避免笛卡尔积）"""
        money = DecimalField(max_digits=10, decimal_places=2)
        inv_sub = models.Invoice.objects.filter(contract=OuterRef('pk'), is_delete=False).values('contract').annotate(
            total=Sum('amount')).values('total')
        col_sub = models.Collection.objects.filter(contract=OuterRef('pk'), is_delete=False).values('contract').annotate(
            total=Sum('amount')).values('total')
        base = (
            models.Contract.objects.filter(is_delete=False)
            .select_related('customer', 'customer__saler')
            .annotate(
                invoiced_amount=Coalesce(Subquery(inv_sub, output_field=money), Value(Decimal('0'), output_field=money), output_field=money),
                collected_amount=Coalesce(Subquery(col_sub, output_field=money), Value(Decimal('0'), output_field=money), output_field=money),
            )
        )
        customer_name = (request.query_params.get('customer_name') or '').strip()
        if customer_name:
            base = base.filter(customer__company_name__icontains=customer_name)
        salesperson = (request.query_params.get('salesperson') or '').strip()
        if salesperson:
            try:
                sid = int(salesperson)
            except (TypeError, ValueError):
                sid = 0
            if sid:
                base = base.filter(customer__saler_id=sid)

        invoiced_unpaid = base.filter(
            invoiced_amount__gt=0,
            collected_amount__lt=F('total_price'),
        ).order_by('-date', '-order_number')
        uninvoiced_unpaid = base.filter(
            invoiced_amount=0,
            collected_amount__lt=F('total_price'),
        ).order_by('-date', '-order_number')

        def _rows(qs):
            out = []
            for c in qs:
                inv_date = models.Invoice.objects.filter(contract=c, is_delete=False).order_by('-date').values_list('date', flat=True).first()
                total = float(c.total_price or 0)
                inv_amt = float(c.invoiced_amount or 0)
                col_amt = float(c.collected_amount or 0)
                out.append({
                    'id': c.id,
                    'contract_number': c.contract_number,
                    'date': c.date.strftime('%Y-%m-%d') if c.date else '',
                    'customer_name': c.customer.company_name,
                    'saler_name': c.customer.saler.username if c.customer.saler_id else '',
                    'total_price': total,
                    'invoiced_amount': inv_amt,
                    'collected_amount': col_amt,
                    'outstanding_balance': total - col_amt,
                    'last_invoice_date': inv_date.strftime('%Y-%m-%d') if inv_date else '',
                    'invoice_ratio': round(inv_amt / total * 100, 2) if total else 0,
                    'collection_ratio': round(col_amt / total * 100, 2) if total else 0,
                })
            return out

        invoiced_rows = _rows(invoiced_unpaid)
        uninvoiced_rows = _rows(uninvoiced_unpaid)

        salespeople = list(
            models.User.objects.filter(
                id__in=models.Customer.objects.filter(is_delete=False).values_list('saler_id', flat=True).distinct()
            ).order_by('username').values('id', 'username')
        )

        return Response({
            'invoiced_unpaid': invoiced_rows,
            'uninvoiced_unpaid': uninvoiced_rows,
            'invoiced_unpaid_count': len(invoiced_rows),
            'uninvoiced_unpaid_count': len(uninvoiced_rows),
            'total_invoiced_outstanding': round(sum(r['outstanding_balance'] for r in invoiced_rows), 2),
            'total_uninvoiced_outstanding': round(sum(r['outstanding_balance'] for r in uninvoiced_rows), 2),
            'salespeople': salespeople,
            'selected_salesperson': salesperson,
            'selected_customer_name': customer_name,
        })

    @action(detail=False, methods=['get'], url_path='charts')
    def charts(self, request):
        """本年度分月合同业绩、合同额前五、业务员销售业绩占比（与原版一致）"""
        today = datetime.date.today()
        year_start = datetime.date(today.year, 1, 1)
        next_year_start = datetime.date(today.year + 1, 1, 1)

        monthly = []
        for month_num in range(1, 13):
            month_start = datetime.date(today.year, month_num, 1)
            next_month_num = month_num + 1 if month_num < 12 else 1
            next_year_num = today.year if month_num < 12 else today.year + 1
            month_end = datetime.date(next_year_num, next_month_num, 1)
            month_total = models.Contract.objects.filter(
                is_delete=False,
                date__gte=month_start,
                date__lt=month_end,
            ).aggregate(total=Sum('total_price'))['total'] or 0
            monthly.append({'month': '{}月'.format(month_num), 'amount': float(month_total)})

        top_customers = models.Contract.objects.filter(
            is_delete=False,
            date__gte=year_start,
            date__lt=next_year_start,
        ).values('customer__company_name').annotate(
            total=Sum('total_price')
        ).order_by('-total')[:5]
        top_customers_data = [
            {'name': item['customer__company_name'], 'value': float(item['total'] or 0)}
            for item in top_customers
        ]

        salesman_sales = models.Contract.objects.filter(
            is_delete=False,
            date__gte=year_start,
            date__lt=next_year_start,
        ).values('customer__saler__username').annotate(
            total=Sum('total_price')
        ).order_by('-total')
        salesman_data = [
            {'name': item['customer__saler__username'] or '未分配', 'value': float(item['total'] or 0)}
            for item in salesman_sales
        ]

        return Response({
            'year': today.year,
            'monthly': monthly,
            'top_customers': top_customers_data,
            'salesman': salesman_data,
        })

    @action(detail=False, methods=['get'], url_path='check-number')
    def check_number(self, request):
        """实时检查合同编号是否重复（与原版 check_contract_number 一致）"""
        contract_number = request.query_params.get('contract_number', '').strip()
        exclude_id = request.query_params.get('exclude_id')
        if not contract_number:
            return Response({'exists': False, 'message': ''})
        # 不排除 is_delete：contract_number 在库里是 unique，软删除的合同仍占号，
        # 排除会让前端以为可用，保存时才撞 UNIQUE 冲突。
        qs = models.Contract.objects.filter(contract_number=contract_number)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        if qs.exists():
            return Response({'exists': True, 'message': '合同编号已存在，请更换后重试。'})
        return Response({'exists': False, 'message': '合同编号可用。'})


    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """合同附件上传（与原版一致：保存到 media/contract/<年份>/）"""
        from django.core.files.storage import default_storage
        from django.conf import settings
        import os
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': '请选择文件'}, status=status.HTTP_400_BAD_REQUEST)
        year = datetime.date.today().year
        folder = os.path.join(settings.MEDIA_ROOT, 'contract', str(year))
        os.makedirs(folder, exist_ok=True)
        filename = f.name
        # 防止路径穿越
        filename = os.path.basename(filename)
        path = os.path.join('contract', str(year), filename)
        saved = default_storage.save(path, f)
        return Response({'attachment': saved, 'name': f.name})

    def _collect_product_rows(self, products, customer):
        """校验并整理产品明细，返回 (rows, quantity, total_price)。

        数量必须 >=1、单价必须 >=0：老版模型 quantity 带 MinValueValidator(1)，
        这里绕过 ModelForm 直接建对象，必须自己校验，否则能存出 0/负数金额的合同。
        """
        valid_products = [p for p in products if p.get('category') and p.get('product')]
        if not valid_products:
            raise ValueError('请至少添加一条有效的产品明细')

        rows = []
        quantity = 0
        total_price = Decimal('0.00')
        for p in valid_products:
            try:
                qty = int(p.get('quantity') or 0)
            except (TypeError, ValueError):
                raise ValueError('产品数量必须是整数')
            if qty < 1:
                raise ValueError('产品数量必须大于 0')
            try:
                price = Decimal(str(p.get('price') or 0))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError('产品单价格式不正确')
            if price < 0:
                raise ValueError('产品单价不能为负数')
            amount = (Decimal(qty) * price).quantize(Decimal('0.01'))
            rows.append({
                'category_id': int(p['category']),
                'product_id': int(p['product']),
                'contract_type': p.get('contract_type', 'sale'),
                'quantity': qty,
                'price': price,
                'total_price': amount,
                'description': p.get('description') or '',
            })
            quantity += qty
            total_price += amount
        return rows, quantity, total_price

    def create(self, request, *args, **kwargs):
        """新增合同：支持基础信息 + 产品明细，事务保存，自动计算数量/金额（与原版一致）"""
        data = request.data
        customer_id = data.get('customer')
        customer = models.Customer.objects.filter(id=customer_id).first() if customer_id else None
        if not customer:
            return Response({'detail': '请先选择客户名称'}, status=status.HTTP_400_BAD_REQUEST)

        contract_number = (data.get('contract_number') or '').strip()
        if not contract_number:
            return Response({'detail': '请输入合同编号'}, status=status.HTTP_400_BAD_REQUEST)
        if models.Contract.objects.filter(contract_number=contract_number).exists():
            return Response({'detail': '合同编号已存在，请更换后重试。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rows, quantity, total_price = self._collect_product_rows(
                data.get('products') or [], customer)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                order_number = (models.Contract.objects.aggregate(
                    last_number=Max('order_number'))['last_number'] or 0) + 1
                attach_file = request.FILES.get('attachment')
                contract = models.Contract(
                    order_number=order_number,
                    date=data.get('date') or datetime.date.today(),
                    customer=customer,
                    contract_number=contract_number,
                    remark=data.get('remark') or '',
                )
                if attach_file:
                    contract.attachment = attach_file
                elif data.get('attachment'):
                    contract.attachment = data.get('attachment')

                contract.quantity = quantity
                contract.total_price = total_price
                contract.save()

                for row in rows:
                    models.Contract_Product(contract=contract, customer=customer, **row).save()

            serializer = self.get_serializer(contract)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': f'保存失败：{e}'}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """编辑合同：支持基础信息 + 产品明细整体替换"""
        instance = self.get_object()
        data = request.data
        customer_id = data.get('customer')
        customer = models.Customer.objects.filter(id=customer_id).first() if customer_id else instance.customer
        if not customer:
            return Response({'detail': '请先选择客户名称'}, status=status.HTTP_400_BAD_REQUEST)

        contract_number = (data.get('contract_number') or '').strip()
        if not contract_number:
            return Response({'detail': '请输入合同编号'}, status=status.HTTP_400_BAD_REQUEST)
        if models.Contract.objects.filter(
                contract_number=contract_number).exclude(id=instance.id).exists():
            return Response({'detail': '合同编号已存在，请更换后重试。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rows, quantity, total_price = self._collect_product_rows(
                data.get('products') or [], customer)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 合同金额不能降到已回款/已开票金额之下，否则未收金额变负数、
        # 百分比超过 100%，报表和对账都会错乱。
        paid = models.Collection.objects.filter(
            contract=instance, is_delete=False).aggregate(
            total=Sum('amount'))['total'] or 0
        if total_price < paid:
            return Response(
                {'detail': '合同金额不能低于已回款金额（已回款 %.2f 元）' % paid},
                status=status.HTTP_400_BAD_REQUEST)
        invoiced = models.Invoice.objects.filter(
            contract=instance, is_delete=False).aggregate(
            total=Sum('amount'))['total'] or 0
        if total_price < invoiced:
            return Response(
                {'detail': '合同金额不能低于已开票金额（已开票 %.2f 元）' % invoiced},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                instance.date = data.get('date') or instance.date
                instance.customer = customer
                instance.contract_number = contract_number
                instance.remark = data.get('remark') or ''
                attach_file = request.FILES.get('attachment')
                if attach_file:
                    instance.attachment = attach_file
                else:
                    instance.attachment = data.get('attachment') or ''
                instance.quantity = quantity
                instance.total_price = total_price
                instance.save()

                # 删除旧产品，重建
                models.Contract_Product.objects.filter(contract=instance).delete()
                for row in rows:
                    models.Contract_Product(contract=instance, customer=customer, **row).save()

                # 合同金额变化后，回款/开票完结状态必须重算，否则 1000 改成 5000
                # 仍会显示"已付清"，应收报表也随之错误。
                instance.update_payment_completed_status()
                instance.update_invoice_completed_status()

            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            return Response({'detail': f'保存失败：{e}'}, status=status.HTTP_400_BAD_REQUEST)


class ContractProductViewSet(BaseModelViewSet):
    queryset = models.Contract_Product.objects.select_related(
        'contract', 'customer', 'category', 'product').all()
    serializer_class = ContractProductSerializer
    permission_codes = 'contract_product'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contract', 'customer', 'category', 'product']

    def get_queryset(self):
        qs = super().get_queryset()
        # 排除所属合同已软删除的产品明细（合同产品表本身无 is_delete 字段）
        qs = qs.filter(contract__is_delete=False)
        keyword = self.request.query_params.get('keyword')
        if keyword:
            kw = keyword.strip()
            qs = qs.filter(
                Q(customer__company_name__icontains=kw) |
                Q(contract__contract_number__icontains=kw) |
                Q(category__name__icontains=kw) |
                Q(product__model__icontains=kw)
            )
        return qs.order_by('-id')

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """合同产品数据导出 Excel（与原版 contract_product_download_excel 一致）"""
        import pandas as pd
        from io import BytesIO
        from django.http import HttpResponse
        qs = self.get_queryset()
        data = []
        for cp in qs:
            data.append({
                '合同序号': cp.contract.order_number,
                '客户名称': cp.contract.customer.company_name,
                '产品名称': cp.category.name,
                '产品型号': cp.product.model,
                '服务类型': cp.get_contract_type_display(),
                '数量': cp.quantity,
                '单价': cp.price,
                '金额': cp.total_price,
                '已开发票': cp.contract.total_invoice(),
                '已收款': cp.contract.total_collection(),
                '日期': cp.contract.date,
                '合同号': cp.contract.contract_number,
            })
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = "contract_product_data_{}.xlsx".format(datetime.datetime.now().strftime("%Y%m%d%H%M"))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

    @action(detail=False, methods=['get'], url_path='template')
    def template(self, request):
        """下载批量导入模板（从老版 media 目录读取）"""
        from django.http import FileResponse
        import pathlib
        root_media = pathlib.Path(__file__).resolve().parent.parent.parent.parent / 'media'
        template_path = root_media / 'uploadtemplates' / 'contract_product_list.xlsx'
        if not template_path.exists():
            return Response({'detail': '模板文件不存在'}, status=status.HTTP_404_NOT_FOUND)
        response = FileResponse(
            open(template_path, 'rb'),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="contract_product_list.xlsx"'
        return response

    @action(detail=False, methods=['post'], url_path='import')
    def import_excel(self, request):
        """合同产品批量导入 Excel（与原版 contract_product_multi 一致）"""
        import pandas as pd
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': '请选择文件'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            df = pd.read_excel(f)
        except Exception as e:
            return Response({'detail': '文件解析失败：{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)
        company_dict = {s.company_name: s for s in models.Customer.objects.all()}
        contract_dict = {s.contract_number: s for s in models.Contract.objects.all()}
        productcategory_dict = {s.name: s for s in models.ProductCategory.objects.all()}
        product_dict = {s.model: s for s in models.Product.objects.all()}
        success = 0
        errors = []
        try:
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        customer_name = str(row.get('购货单位') or '').strip()
                        contract_number = str(row.get('合同编号') or '').strip()
                        category_name = str(row.get('产品名称') or '').strip()
                        product_model = str(row.get('规格型号') or '').strip()
                        if not (customer_name and contract_number and category_name and product_model):
                            errors.append('第{}行：购货单位/合同编号/产品名称/规格型号不能为空'.format(index + 2))
                            continue
                        customer = company_dict.get(customer_name)
                        contract = contract_dict.get(contract_number)
                        category = productcategory_dict.get(category_name)
                        product = product_dict.get(product_model)
                        if not customer or not contract or not category or not product:
                            errors.append('第{}行：客户/合同/产品/型号未找到'.format(index + 2))
                            continue
                        try:
                            qty = int(row.get('数量') or 0)
                        except (TypeError, ValueError):
                            qty = 0
                        try:
                            price = Decimal(str(row.get('单价') or 0))
                        except (InvalidOperation, TypeError, ValueError):
                            price = Decimal('0.00')
                        try:
                            amount = Decimal(str(row.get('金额') or 0))
                        except (InvalidOperation, TypeError, ValueError):
                            amount = Decimal('0.00')
                        cp = models.Contract_Product(
                            contract=contract,
                            customer=customer,
                            category=category,
                            product=product,
                            contract_type='sale',
                            quantity=qty,
                            price=price,
                            total_price=amount,
                            description='',
                        )
                        cp.save()
                        success += 1
                    except Exception as e:
                        errors.append('第{}行：{}'.format(index + 2, e))
        except Exception as e:
            return Response({'detail': '导入失败：{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)
        message = '成功导入 {} 条'.format(success)
        if errors:
            message += '，{} 条失败（{}）'.format(len(errors), '；'.join(errors[:5]))
        return Response({'detail': message, 'success': success, 'errors': errors})


class CollectionViewSet(BaseModelViewSet):
    queryset = models.Collection.objects.select_related(
        'customer', 'contract', 'contract__customer').all()
    serializer_class = CollectionSerializer
    permission_codes = 'collection_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['contract__contract_number', 'customer__company_name']

    def get_queryset(self):
        qs = super().get_queryset()
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from and date_to:
            qs = qs.filter(date__range=[date_from, date_to])
        elif date_from:
            qs = qs.filter(date__gte=date_from)
        elif date_to:
            qs = qs.filter(date__lte=date_to)
        keyword = self.request.query_params.get('keyword')
        if keyword:
            kw = keyword.strip()
            qs = qs.filter(
                Q(customer__company_name__icontains=kw) |
                Q(contract__contract_number__icontains=kw))
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            qs = qs.filter(contract_id=contract_id)
        return qs.order_by('-date')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """统计：总金额/条目数/本月回款趋势/本季度业务员占比（与原版一致）"""
        import datetime
        qs = self.get_queryset()
        total = qs.aggregate(total=Sum('amount'))['total'] or 0
        count = qs.count()

        today = datetime.date.today()
        months = []
        amounts = []
        for month in range(1, 13):
            month_start = datetime.date(today.year, month, 1)
            month_end = (datetime.date(today.year + 1, 1, 1) if month == 12
                         else datetime.date(today.year, month + 1, 1))
            month_total = models.Collection.objects.filter(
                is_delete=False,
                date__gte=month_start,
                date__lt=month_end,
            ).aggregate(total=Sum('amount'))['total'] or 0
            months.append('{}月'.format(month))
            amounts.append(float(month_total))

        quarter_month = ((today.month - 1) // 3) * 3 + 1
        quarter_start = datetime.date(today.year, quarter_month, 1)
        quarter_end = (datetime.date(today.year + 1, 1, 1) if quarter_month == 10
                       else datetime.date(today.year, quarter_month + 3, 1))
        salesman_sales = models.Collection.objects.filter(
            is_delete=False,
            date__gte=quarter_start,
            date__lt=quarter_end,
        ).values('customer__saler__username').annotate(
            total=Sum('amount')).order_by('-total')
        salesman = [
            {'name': item['customer__saler__username'] or '未分配',
             'value': float(item['total'] or 0)}
            for item in salesman_sales
        ]

        return Response({
            'total_amount': float(total),
            'count': count,
            'monthly': months,
            'monthly_amounts': amounts,
            'quarter_salesman': salesman,
        })

    @action(detail=False, methods=['get'], url_path='contracts')
    def contracts(self, request):
        """获取指定客户的欠款合同（与原版 get_collection_contracts 一致）"""
        from django.db.models import OuterRef, Subquery, Case, When, F, DecimalField
        from decimal import Decimal
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response([])
        paid_sub = models.Collection.objects.filter(
            contract=OuterRef('pk'), is_delete=False
        ).values('contract').annotate(total=Sum('amount')).values('total')[:1]
        contracts = models.Contract.objects.filter(
            customer_id=customer_id, is_delete=False,
        ).annotate(
            total_paid=Subquery(paid_sub),
            balance=Case(
                When(total_paid__isnull=True, then=F('total_price')),
                default=F('total_price') - F('total_paid'),
                output_field=DecimalField(),
            ),
        ).filter(balance__gt=0).values('id', 'contract_number', 'balance')
        return Response(list(contracts))

    @action(detail=False, methods=['get'], url_path='customers')
    def customers(self, request):
        """获取有欠款的客户列表（与原版 get_collection_customers 一致）"""
        from django.db.models import OuterRef, Subquery, Case, When, F, DecimalField
        query = request.query_params.get('q', '').strip()
        paid_sub = models.Collection.objects.filter(
            contract=OuterRef('pk'), is_delete=False
        ).values('contract').annotate(total=Sum('amount')).values('total')[:1]
        contracts = models.Contract.objects.filter(is_delete=False).annotate(
            total_paid=Subquery(paid_sub),
            balance=Case(
                When(total_paid__isnull=True, then=F('total_price')),
                default=F('total_price') - F('total_paid'),
                output_field=DecimalField(),
            ),
        ).filter(balance__gt=0)
        if query:
            contracts = contracts.filter(customer__company_name__icontains=query)
        result = list(contracts.values('customer_id', 'customer__company_name').distinct()[:20])
        return Response([
            {'id': r['customer_id'], 'company_name': r['customer__company_name']}
            for r in result
        ])

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """回款数据导出 Excel（与原版 collection_download_excel 一致）"""
        import pandas as pd
        from io import BytesIO
        from django.http import HttpResponse
        qs = self.get_queryset()
        data = [{
            '回款日期': c.date,
            '客户名称': c.customer.company_name,
            '合同号码': c.contract.contract_number,
            '合同金额': c.contract.total_price,
            '回款金额': c.amount,
            '回款方式': c.get_collection_method_display(),
            '回款比例': '{:.2f}%'.format(c.contract.collection_ratio()),
            '业务经理': c.customer.saler.username,
        } for c in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'collection_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response


class InvoiceViewSet(BaseModelViewSet):
    queryset = models.Invoice.objects.select_related(
        'customer', 'contract', 'invoice_man').all()
    serializer_class = InvoiceSerializer
    permission_codes = 'invoice_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['invoice_number', 'contract__contract_number', 'customer__company_name']

    def get_queryset(self):
        qs = super().get_queryset()
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from and date_to:
            qs = qs.filter(date__range=[date_from, date_to])
        elif date_from:
            qs = qs.filter(date__gte=date_from)
        elif date_to:
            qs = qs.filter(date__lte=date_to)
        keyword = self.request.query_params.get('keyword')
        if keyword:
            kw = keyword.strip()
            qs = qs.filter(
                Q(customer__company_name__icontains=kw) |
                Q(contract__contract_number__icontains=kw) |
                Q(invoice_number__icontains=kw))
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            qs = qs.filter(contract_id=contract_id)
        return qs.order_by('-date')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """统计：本年度每月开票额/年度前五/本月前五占比（与原版一致）"""
        import datetime
        qs = self.get_queryset()
        total = qs.aggregate(total=Sum('amount'))['total'] or 0
        count = qs.count()

        today = datetime.date.today()
        year_start = datetime.date(today.year, 1, 1)
        next_year_start = datetime.date(today.year + 1, 1, 1)
        month_start = datetime.date(today.year, today.month, 1)
        next_month_start = (datetime.date(today.year + 1, 1, 1)
                            if today.month == 12
                            else datetime.date(today.year, today.month + 1, 1))

        months = []
        amounts = []
        for month in range(1, 13):
            current_start = datetime.date(today.year, month, 1)
            current_end = (datetime.date(today.year + 1, 1, 1) if month == 12
                           else datetime.date(today.year, month + 1, 1))
            month_total = models.Invoice.objects.filter(
                is_delete=False, date__gte=current_start, date__lt=current_end,
            ).aggregate(total=Sum('amount'))['total'] or 0
            months.append('{}月'.format(month))
            amounts.append(float(month_total))

        top_customers = models.Invoice.objects.filter(
            is_delete=False, date__gte=year_start, date__lt=next_year_start,
        ).values('customer__company_name').annotate(total=Sum('amount')).order_by('-total')[:5]
        top_customers_data = [
            {'name': item['customer__company_name'], 'value': float(item['total'] or 0)}
            for item in top_customers
        ]

        month_customers = models.Invoice.objects.filter(
            is_delete=False, date__gte=month_start, date__lt=next_month_start,
        ).values('customer__company_name').annotate(total=Sum('amount')).order_by('-total')[:5]
        month_customers_data = [
            {'name': item['customer__company_name'], 'value': float(item['total'] or 0)}
            for item in month_customers
        ]

        return Response({
            'total_amount': float(total),
            'count': count,
            'monthly': months,
            'monthly_amounts': amounts,
            'year_top_customers': top_customers_data,
            'month_top_customers': month_customers_data,
        })

    @action(detail=False, methods=['get'], url_path='contracts')
    def contracts(self, request):
        """获取指定客户的未完结发票合同（与原版 get_invoice_contracts 一致）"""
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response([])
        contracts = models.Contract.objects.filter(
            customer_id=customer_id, is_delete=False, invoice_completed=False,
        ).values('id', 'contract_number')
        return Response(list(contracts))

    @action(detail=False, methods=['get'], url_path='customers')
    def customers(self, request):
        """获取有未完结发票的客户列表（与原版 invoice_create 一致）"""
        from django.db.models import Exists, OuterRef
        query = request.query_params.get('q', '').strip()
        customers = models.Customer.objects.filter(
            Exists(models.Contract.objects.filter(
                customer=OuterRef('pk'), is_delete=False, invoice_completed=False)))
        if query:
            customers = customers.filter(company_name__icontains=query)
        customers = customers.order_by('company_name')[:20]
        return Response([
            {'id': c.id, 'company_name': c.company_name} for c in customers
        ])

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """发票数据导出 Excel"""
        import pandas as pd
        from io import BytesIO
        from django.http import HttpResponse
        qs = self.get_queryset()
        data = [{
            '开票日期': i.date,
            '客户名称': i.customer.company_name,
            '合同号码': i.contract.contract_number,
            '发票号': i.invoice_number,
            '开票金额': i.amount,
            '开票人': i.invoice_man.username,
        } for i in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'invoice_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

    @action(detail=False, methods=['get'], url_path='template')
    def template(self, request):
        """下载批量导入模板 fapiao.xlsx"""
        from django.http import FileResponse
        import pathlib
        root_media = pathlib.Path(__file__).resolve().parent.parent.parent.parent / 'media'
        template_path = root_media / 'uploadtemplates' / 'fapiao.xlsx'
        if not template_path.exists():
            return Response({'detail': '模板文件不存在'}, status=status.HTTP_404_NOT_FOUND)
        response = FileResponse(
            open(template_path, 'rb'),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="fapiao.xlsx"'
        return response

    def _parse_invoice_records(self, frame):
        """解析发票 Excel，返回 (records, error)。

        支持两种格式：
        1. 金蝶销售发票序时簿：多行结构，一张发票多行产品明细，
           日期/发票号码/购货单位/订单单号只写在首行，需向下填充；
           开票金额取「价税合计」，同一订单单号下多行价税合计合并求和。
        2. 简单模板：每行一条记录，金额取「开票金额」或「金额」。
        """
        import pandas as pd

        def clean(value):
            if value is None:
                return ''
            try:
                if pd.isna(value):
                    return ''
            except (TypeError, ValueError):
                pass
            text = str(value).strip()
            return '' if text.lower() in ('nan', 'nat', 'none') else text

        kingdee_amount_column = '价税合计'
        if kingdee_amount_column in frame.columns and '产品名称' in frame.columns:
            # 金蝶销售发票序时簿
            work = frame.copy()
            work['_row_no'] = work.index + 2
            mask = work['产品名称'].notna()
            if '审核标志' in work.columns:
                mask &= ~work['审核标志'].astype(str).str.contains('合计', na=False)
            work = work[mask].copy()
            if work.empty:
                return None, '未在文件中找到发票数据'
            key_columns = ['日期', '发票号码', '购货单位', '订单单号']
            work[key_columns] = work[key_columns].ffill()
            records = []
            for order_number, group in work.groupby('订单单号', sort=False):
                row_no = int(group['_row_no'].iloc[0])
                number = clean(group['发票号码'].iloc[0])
                numbers = {clean(v) for v in group['发票号码']}
                numbers.discard('')
                record = {
                    'row_no': row_no,
                    'invoice_number': number,
                    'contract_number': clean(order_number),
                    'customer_name': clean(group['购货单位'].iloc[0]),
                    'date': group['日期'].iloc[0],
                    'amount': group[kingdee_amount_column].sum(),
                    'errors': [],
                }
                if len(numbers) > 1:
                    record['errors'].append(
                        '订单单号 {} 对应多个发票号码'.format(clean(order_number)))
                records.append(record)
            return records, None
        elif '开票金额' in frame.columns or '金额' in frame.columns:
            # 简单模板
            records = []
            for index, row in frame.iterrows():
                records.append({
                    'row_no': int(index) + 2,
                    'invoice_number': clean(row.get('发票号码') or row.get('发票号')),
                    'contract_number': clean(row.get('订单单号')),
                    'customer_name': clean(row.get('购货单位')),
                    'date': row.get('日期') or row.get('开票日期'),
                    'amount': row.get('开票金额') or row.get('金额') or 0,
                    'errors': [],
                })
            return records, None
        return None, '文件格式不正确，缺少发票号码、购货单位、订单单号、金额等列'

    @action(detail=False, methods=['post'], url_path='preview')
    def preview_excel(self, request):
        """发票批量导入预览：上传前数据校验"""
        import pandas as pd
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': '请选择文件'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            frame = pd.read_excel(f, sheet_name=0)
        except Exception as e:
            return Response({'detail': '文件解析失败：{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

        records, error = self._parse_invoice_records(frame)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        contract_dict = {s.contract_number: s for s in models.Contract.objects.all()}
        customer_dict = {s.company_name.strip(): s for s in models.Customer.objects.all()}
        existing_invoice_numbers = set(models.Invoice.objects.values_list('invoice_number', flat=True))

        rows = []
        seen_invoice_numbers = set()
        for record in records:
            row_no = record['row_no']
            number = record['invoice_number']
            errors = list(record['errors'])

            if not number:
                errors.append('发票号码为空')
            elif number in existing_invoice_numbers:
                errors.append('发票号码已存在')
            elif number in seen_invoice_numbers:
                errors.append('发票号码重复')
            else:
                seen_invoice_numbers.add(number)

            contract_number = record['contract_number']
            contract = contract_dict.get(contract_number) if contract_number else None
            if not contract_number:
                errors.append('订单单号为空')
            elif contract is None:
                errors.append('合同不存在：{}'.format(contract_number))

            customer_name = record['customer_name']
            customer = customer_dict.get(customer_name) if customer_name else None
            if not customer_name:
                errors.append('购货单位为空')
            elif customer is None:
                errors.append('客户不存在：{}'.format(customer_name))
            elif contract is not None and contract.customer_id != customer.id:
                errors.append('购货单位与订单单号对应的客户不一致')

            amount = record['amount']
            try:
                amount_val = float(amount) if amount else 0
                if amount_val <= 0:
                    errors.append('金额必须大于0')
            except (ValueError, TypeError):
                errors.append('金额格式错误')
                amount_val = 0

            parsed_date = None
            date = record['date']
            if not date or (isinstance(date, float) and pd.isna(date)):
                errors.append('日期为空')
            else:
                try:
                    if hasattr(date, 'to_pydatetime'):
                        parsed_date = date.to_pydatetime().date()
                    elif isinstance(date, datetime.datetime):
                        parsed_date = date.date()
                    elif isinstance(date, datetime.date):
                        parsed_date = date
                    elif isinstance(date, str):
                        parsed_date = datetime.datetime.strptime(date.strip(), '%Y-%m-%d').date()
                except Exception:
                    errors.append('日期格式错误')

            rows.append({
                'row_no': row_no,
                'contract_number': contract_number,
                'invoice_number': number,
                'amount': round(amount_val, 2),
                'date': str(parsed_date) if parsed_date else '',
                'customer_name': customer_name,
                'errors': errors,
            })

        has_error = any(r['errors'] for r in rows)
        return Response({
            'rows': rows,
            'has_error': has_error,
            'total': len(rows),
        })

    @action(detail=False, methods=['post'], url_path='import')
    def import_excel(self, request):
        """发票批量导入 Excel（支持金蝶销售发票序时簿导出文件）"""
        import pandas as pd
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': '请选择文件'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            frame = pd.read_excel(f, sheet_name=0)
        except Exception as e:
            return Response({'detail': '文件解析失败：{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

        records, error = self._parse_invoice_records(frame)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        contract_dict = {s.contract_number: s for s in models.Contract.objects.all()}
        customer_dict = {s.company_name.strip(): s for s in models.Customer.objects.all()}
        existing_invoice_numbers = set(models.Invoice.objects.values_list('invoice_number', flat=True))
        default_man = models.User.objects.order_by('id').first()

        success = 0
        errors = []
        seen_invoice_numbers = set()
        try:
            with transaction.atomic():
                for record in records:
                    row_no = record['row_no']
                    number = record['invoice_number']
                    try:
                        if not number:
                            errors.append('第{}行：发票号码为空'.format(row_no))
                            continue
                        if number in existing_invoice_numbers:
                            errors.append('第{}行：发票号码 {} 已存在'.format(row_no, number))
                            continue
                        if number in seen_invoice_numbers:
                            errors.append('第{}行：发票号码 {} 重复'.format(row_no, number))
                            continue

                        contract_number = record['contract_number']
                        contract = contract_dict.get(contract_number) if contract_number else None
                        if not contract_number:
                            errors.append('第{}行：订单单号为空'.format(row_no))
                            continue
                        if contract is None:
                            errors.append('第{}行：合同 {} 未找到'.format(row_no, contract_number))
                            continue

                        customer_name = record['customer_name']
                        customer = customer_dict.get(customer_name) if customer_name else None
                        if not customer_name:
                            errors.append('第{}行：购货单位为空'.format(row_no))
                            continue
                        if customer is None:
                            errors.append('第{}行：客户 {} 未找到'.format(row_no, customer_name))
                            continue
                        if contract.customer_id != customer.id:
                            errors.append('第{}行：购货单位与订单单号对应的客户不一致'.format(row_no))
                            continue

                        date = record['date']
                        if not date or (isinstance(date, float) and pd.isna(date)):
                            errors.append('第{}行：开票日期为空'.format(row_no))
                            continue
                        if hasattr(date, 'to_pydatetime'):
                            date = date.to_pydatetime().date()
                        elif isinstance(date, datetime.datetime):
                            date = date.date()
                        elif isinstance(date, datetime.date):
                            pass
                        elif isinstance(date, str):
                            date = datetime.datetime.strptime(date.strip(), '%Y-%m-%d').date()

                        try:
                            amount_val = Decimal(str(round(float(record['amount']), 2)))
                        except (InvalidOperation, ValueError, TypeError):
                            errors.append('第{}行：金额格式错误'.format(row_no))
                            continue

                        inv = models.Invoice(
                            date=date,
                            customer=customer,
                            contract=contract,
                            invoice_number=number,
                            amount=amount_val,
                            invoice_man=default_man,
                        )
                        inv.save()
                        seen_invoice_numbers.add(number)
                        success += 1
                    except Exception as e:
                        errors.append('第{}行：{}'.format(row_no, e))
        except Exception as e:
            return Response({'detail': '导入失败：{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

        message = '成功导入 {} 条'.format(success)
        if errors:
            message += '，{} 条失败（{}）'.format(len(errors), '；'.join(errors[:5]))
        return Response({'detail': message, 'success': success, 'errors': errors})

    def create(self, request, *args, **kwargs):
        """新增发票：自动带出客户、开票人"""
        data = request.data
        contract_id = data.get('contract')
        contract = models.Contract.objects.filter(id=contract_id).first() if contract_id else None
        if not contract:
            return Response({'detail': '请选择合同编号'}, status=status.HTTP_400_BAD_REQUEST)
        invoice_number = (data.get('invoice_number') or '').strip()
        if not invoice_number:
            return Response({'detail': '请输入发票号码'}, status=status.HTTP_400_BAD_REQUEST)
        if not data.get('date'):
            return Response({'detail': '请选择开票日期'}, status=status.HTTP_400_BAD_REQUEST)

        # 走 serializer 才能复用金额校验（>0 且不超过合同总额），不能直接 instance.save()
        payload = dict(data)
        payload['customer'] = contract.customer_id
        payload['invoice_man'] = request.user.pk
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
