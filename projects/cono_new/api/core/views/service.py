"""售后体系：售后服务/维修服务/售后返件"""
import datetime
from io import BytesIO
from django.db.models import Q, Count, Sum, Exists, OuterRef
from django.http import HttpResponse
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from api.core import models
from api.core.flow_bridge import complete_archive_repair, reopen_archive_repair
from api.core.serializers.common import (
    ServiceSerializer, ServiceDetailSerializer, ReturnProductSerializer,
)
from api.core.views.base import BaseModelViewSet, DROPDOWN_SEARCH_LIMIT


class ServiceViewSet(BaseModelViewSet):
    queryset = models.Service.objects.select_related(
        'customer', 'productcategory', 'product', 'repairman').all()
    serializer_class = ServiceSerializer
    permission_codes = 'service_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['service_number', 'product_number']

    def get_queryset(self):
        qs = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            qs = qs.filter(date__range=(start_date, end_date))
        customer_name = self.request.query_params.get('customer_name')
        if customer_name:
            qs = qs.filter(customer__company_name__icontains=customer_name.strip())
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(
                Q(product__model__icontains=keyword.strip()) |
                Q(productcategory__name__icontains=keyword.strip()))
        return qs.order_by('-id')

    @action(detail=False, methods=['get'], url_path='charts')
    def charts(self, request):
        """售后列表三张图表数据（本年度每月/近三年对比/客户前五占比）"""
        today = datetime.date.today()
        chart_months = []
        chart_month_values = []
        for month in range(1, 13):
            month_start = datetime.date(today.year, month, 1)
            month_end = (datetime.date(today.year + 1, 1, 1)
                         if month == 12 else datetime.date(today.year, month + 1, 1))
            count = models.Service.objects.filter(
                is_delete=False, date__gte=month_start, date__lt=month_end).count()
            chart_months.append('{}月'.format(month))
            chart_month_values.append(count)

        chart_three_years = []
        for year in (today.year - 2, today.year - 1, today.year):
            values = []
            for month in range(1, 13):
                month_start = datetime.date(year, month, 1)
                month_end = (datetime.date(year + 1, 1, 1)
                             if month == 12 else datetime.date(year, month + 1, 1))
                values.append(models.Service.objects.filter(
                    is_delete=False, date__gte=month_start, date__lt=month_end).count())
            chart_three_years.append({'year': year, 'values': values})

        year_start = datetime.date(today.year, 1, 1)
        next_year_start = datetime.date(today.year + 1, 1, 1)
        customer_counts = models.Service.objects.filter(
            is_delete=False, date__gte=year_start, date__lt=next_year_start,
        ).values('customer__company_name').annotate(cnt=Count('id')).order_by('-cnt')
        top_customers = list(customer_counts[:5])
        total_count = sum(item['cnt'] for item in customer_counts)
        top_count = sum(item['cnt'] for item in top_customers)
        labels = [item['customer__company_name'] for item in top_customers]
        values = [item['cnt'] for item in top_customers]
        if total_count - top_count > 0:
            labels.append('其他')
            values.append(total_count - top_count)

        return Response({
            'chart_months': chart_months,
            'chart_month_values': chart_month_values,
            'chart_three_years': chart_three_years,
            'chart_customer_labels': labels,
            'chart_customer_values': values,
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """售后服务数据导出 Excel（与原版 service_download_excel 一致）"""
        import pandas as pd
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        data = [{
            '接收日期': s.date,
            '客户名称': s.customer.company_name if s.customer else '',
            '产品名称': s.productcategory.name if s.productcategory else '',
            '产品型号': s.product.model if s.product else '',
            '产品编号': s.product_number or '',
            '维修编号': s.service_number,
            '责任人': s.repairman.username if s.repairman else '',
        } for s in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'service_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

    @action(detail=False, methods=['get'], url_path='next-number')
    def next_number(self, request):
        last = models.Service.objects.order_by('-id').first()
        next_id = (last.id if last else 0) + 1
        return Response({'service_number': 'CN2025WX{:03d}'.format(next_id)})

    @action(detail=False, methods=['get'], url_path='customers')
    def customers(self, request):
        """售后服务新增/编辑的客户下拉：搜索全部客户。

        老版 service_add/service_edit 用的是 search_companys（全量搜索）。这里若按
        「已有售后记录」过滤，从未报修过的客户永远选不到，也就无法为其登记首单。
        """
        query = request.query_params.get('q', '').strip()
        customers = models.Customer.objects.filter(is_delete=False)
        if query:
            customers = customers.filter(company_name__icontains=query)
        customers = customers.order_by('company_name')[:DROPDOWN_SEARCH_LIMIT]
        return Response([{'id': c.id, 'company_name': c.company_name} for c in customers])

    def create(self, request, *args, **kwargs):
        data = request.data
        if not data.get('service_number'):
            last = models.Service.objects.order_by('-id').first()
            next_id = (last.id if last else 0) + 1
            data['service_number'] = 'CN2025WX{:03d}'.format(next_id)
        try:
            user = request.user
            data['repairman'] = user.id
        except Exception:
            pass
        return super().create(request, *args, **kwargs)


class ServiceDetailViewSet(BaseModelViewSet):
    queryset = models.ServiceDetail.objects.select_related(
        'customer', 'service', 'service__customer', 'service__productcategory',
        'service__product', 'productcategory', 'product', 'repairman').all()
    serializer_class = ServiceDetailSerializer
    permission_codes = 'servicedetail_list'

    def get_queryset(self):
        qs = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            qs = qs.filter(repair_date__range=(start_date, end_date))
        customer_name = self.request.query_params.get('customer_name')
        if customer_name:
            qs = qs.filter(customer__company_name__icontains=customer_name.strip())
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(
                Q(product__model__icontains=keyword.strip()) |
                Q(productcategory__name__icontains=keyword.strip()) |
                Q(service__product_number__icontains=keyword.strip()))
        return qs.order_by('-id')

    @action(detail=False, methods=['get'], url_path='charts')
    def charts(self, request):
        """维修记录三张图表（本年度每月/近三年对比/本月维修人员占比）"""
        today = datetime.date.today()
        chart_months = []
        chart_month_values = []
        for month in range(1, 13):
            month_start = datetime.date(today.year, month, 1)
            month_end = (datetime.date(today.year + 1, 1, 1)
                         if month == 12 else datetime.date(today.year, month + 1, 1))
            count = models.ServiceDetail.objects.filter(
                is_delete=False, repair_date__gte=month_start, repair_date__lt=month_end).count()
            chart_months.append('{}月'.format(month))
            chart_month_values.append(count)

        chart_three_years = []
        for year in (today.year - 2, today.year - 1, today.year):
            values = []
            for month in range(1, 13):
                month_start = datetime.date(year, month, 1)
                month_end = (datetime.date(year + 1, 1, 1)
                             if month == 12 else datetime.date(year, month + 1, 1))
                values.append(models.ServiceDetail.objects.filter(
                    is_delete=False, repair_date__gte=month_start, repair_date__lt=month_end).count())
            chart_three_years.append({'year': year, 'values': values})

        month_start = datetime.date(today.year, today.month, 1)
        next_month_start = (datetime.date(today.year + 1, 1, 1)
                            if today.month == 12 else datetime.date(today.year, today.month + 1, 1))
        repairman_counts = models.ServiceDetail.objects.filter(
            is_delete=False, repair_date__gte=month_start, repair_date__lt=next_month_start,
        ).values('repairman__username').annotate(cnt=Count('id')).order_by('-cnt')
        labels = [item['repairman__username'] for item in repairman_counts]
        values = [item['cnt'] for item in repairman_counts]

        return Response({
            'chart_months': chart_months,
            'chart_month_values': chart_month_values,
            'chart_three_years': chart_three_years,
            'chart_repairman_labels': labels,
            'chart_repairman_values': values,
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """维修服务数据导出"""
        import pandas as pd
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        data = [{
            '客户名称': s.customer.company_name if s.customer else '',
            '维修编号': s.service.service_number if s.service else '',
            '产品名称': s.productcategory.name if s.productcategory else '',
            '产品型号': s.product.model if s.product else '',
            '质保情况': s.service.get_warranty_display() if s.service else '',
            '维修人': s.repairman.username if s.repairman else '',
            '接收时间': s.service.date if s.service else '',
            '维修完成时间': s.repair_date,
            '故障现象': s.fault_text,
            '故障原因': s.fault_reason,
            '维修方法': s.repair_method,
        } for s in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'servicedetail_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

    @action(detail=False, methods=['get'], url_path='customers')
    def customers(self, request):
        """获取有待维修的客户列表（warranty_end=1）"""
        query = request.query_params.get('q', '').strip()
        customers = models.Customer.objects.filter(
            Exists(models.Service.objects.filter(
                customer=OuterRef('pk'), is_delete=False, warranty_end=1)))
        if query:
            customers = customers.filter(company_name__icontains=query)
        customers = customers.order_by('company_name')[:DROPDOWN_SEARCH_LIMIT]
        return Response([{'id': c.id, 'company_name': c.company_name} for c in customers])

    @action(detail=False, methods=['get'], url_path='services')
    def services(self, request):
        """获取指定客户的待维修服务（warranty_end=1）"""
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response([])
        services = models.Service.objects.filter(
            Q(customer_id=customer_id) & Q(is_delete=False) & Q(warranty_end=1)
        ).values('id', 'service_number', 'productcategory_id', 'productcategory__name',
                 'product_id', 'product__model')
        return Response(list(services))

    @action(detail=False, methods=['get'], url_path='knowledge')
    def knowledge(self, request):
        """维修知识库：按故障现象检索历史案例并归纳维修方法。"""
        import re
        from collections import Counter

        query = (request.query_params.get('q') or '').strip()
        if not query:
            return Response({'query': '', 'cases': [], 'summary': None})

        NOISE_VALUES = {
            '', '/', '\\', 'null', 'none', '无', '没有', 'na', 'n/a', '-', '--', '测试正常',
            '重测ok', '测试ok', '正常', '报废', '待定', '未知',
        }

        def _normalize(text):
            text = str(text or '')
            text = re.sub(r'[\s\u3000]+', '', text)
            text = re.sub(r'[，。、；：！？,.;:!?()（）\[\]【】{}<>《》"\'`~@#$%^&*+=|\\/_-]+', '', text)
            return text.lower()

        def is_noise(text):
            return _normalize(text) in {_normalize(v) for v in NOISE_VALUES}

        def _bigrams(text):
            if len(text) < 2:
                return {text} if text else set()
            return {text[i:i + 2] for i in range(len(text) - 1)}

        def similarity(left, right):
            a, b = _bigrams(left), _bigrams(right)
            if not a or not b:
                return 0.0
            return 2 * len(a & b) / (len(a) + len(b))

        def search_cases(query_norm, limit=20):
            matched = []
            for row in models.ServiceDetail.objects.select_related(
                'customer', 'product', 'productcategory', 'repairman', 'service'
            ).filter(is_delete=False).all():
                fault = _normalize(row.fault_text)
                if not fault or is_noise(row.fault_text):
                    continue
                score = similarity(query_norm, fault)
                if query_norm in fault:
                    score = max(score, 0.8)
                if score >= 0.34:
                    matched.append((score, row))
            matched.sort(key=lambda item: (-item[0], -item[1].id))
            return [{'score': round(score, 3), 'record': row} for score, row in matched[:limit]]

        def _cluster(counter, samples):
            ordered = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
            clusters = []
            for key, count in ordered:
                placed = False
                for cluster in clusters:
                    if similarity(key, cluster['key']) >= 0.62:
                        cluster['count'] += count
                        if count > cluster['best_count']:
                            cluster['best_count'] = count
                            cluster['text'] = samples[key]
                        placed = True
                        break
                if not placed:
                    clusters.append({
                        'key': key, 'text': samples[key], 'count': count, 'best_count': count,
                    })
            clusters.sort(key=lambda c: -c['count'])
            return [{'text': c['text'], 'count': c['count']} for c in clusters[:5]]

        def summarize(cases):
            reasons = Counter()
            methods = Counter()
            reason_samples = {}
            method_samples = {}
            for case in cases:
                row = case['record']
                reason = str(row.fault_reason or '').strip()
                method = str(row.repair_method or '').strip()
                if reason and not is_noise(reason):
                    key = _normalize(reason)
                    reasons[key] += 1
                    reason_samples.setdefault(key, reason)
                if method and not is_noise(method):
                    key = _normalize(method)
                    methods[key] += 1
                    method_samples.setdefault(key, method)
            return {
                'total': len(cases),
                'reasons': _cluster(reasons, reason_samples),
                'methods': _cluster(methods, method_samples),
            }

        query_norm = _normalize(query)
        cases = search_cases(query_norm)
        summary = summarize(cases) if cases else None
        # Serialize cases
        case_list = []
        for case in cases:
            row = case['record']
            case_list.append({
                'score': case['score'],
                'service_number': row.service.service_number if row.service else '',
                'customer_name': row.customer.company_name if row.customer else '',
                'product_model': row.product.model if row.product else '',
                'repair_date': str(row.repair_date),
                'fault_text': row.fault_text,
                'fault_reason': row.fault_reason,
                'repair_method': row.repair_method,
            })
        return Response({'query': query, 'cases': case_list, 'summary': summary})

    @action(detail=False, methods=['post'], url_path='batch')
    def batch_create(self, request):
        """批量维修登记：一次为多个待维修产品创建维修记录。"""
        data = request.data
        customer_id = data.get('customer')
        repair_date = data.get('repair_date')
        items = data.get('items') or []
        if not customer_id:
            return Response({'detail': '请选择客户名称'}, status=400)
        if not repair_date:
            return Response({'detail': '请选择维修完成时间'}, status=400)
        if not any(i.get('service') for i in items):
            return Response({'detail': '该项目暂无待维修产品'}, status=400)

        try:
            user = request.user
            user_id = user.id
        except Exception:
            user_id = None

        created = 0
        errors = []
        for item in items:
            service_id = item.get('service')
            if not service_id:
                continue
            if not item.get('fault_text') or not item.get('fault_reason') or not item.get('repair_method'):
                errors.append('故障现象、故障原因、维修方法均不能为空')
                break
            service = models.Service.objects.filter(
                pk=service_id, customer_id=customer_id, is_delete=False, warranty_end=1).first()
            if service is None:
                errors.append('该项目暂无待维修产品')
                break
            models.ServiceDetail.objects.create(
                customer_id=customer_id,
                service_id=service_id,
                productcategory_id=item.get('productcategory') or service.productcategory_id,
                product_id=item.get('product') or service.product_id,
                repairman_id=user_id,
                fault_text=item.get('fault_text'),
                fault_reason=item.get('fault_reason'),
                repair_method=item.get('repair_method'),
                repair_date=repair_date,
            )
            models.Service.objects.filter(pk=service_id).update(warranty_end=2)
            created += 1
        if errors:
            return Response({'detail': errors[0]}, status=400)
        return Response({'created': created})

    def create(self, request, *args, **kwargs):
        data = request.data
        try:
            user = request.user
            data['repairman'] = user.id
        except Exception:
            pass
        instance = super().create(request, *args, **kwargs)
        # 更新 Service 的售后完结状态
        service_id = request.data.get('service')
        if service_id:
            models.Service.objects.filter(pk=service_id).update(warranty_end=2)
        return instance

    def perform_update(self, serializer):
        if not serializer.validated_data.get('repairman'):
            serializer.validated_data['repairman'] = serializer.instance.repairman or self.request.user
        super().perform_update(serializer)

    def destroy(self, request, *args, **kwargs):
        """删除维修记录后，维修单回到「正在维修」，否则售后服务列表会一直显示维修完成。"""
        instance = self.get_object()
        service_id = instance.service_id
        result = super().destroy(request, *args, **kwargs)
        still_repaired = models.ServiceDetail.objects.filter(
            service_id=service_id, is_delete=False).exists()
        if not still_repaired:
            models.Service.objects.filter(pk=service_id).update(warranty_end=1)
        return result


class ReturnProductViewSet(BaseModelViewSet):
    queryset = models.ReturnProduct.objects.select_related(
        'customer', 'service', 'service__productcategory', 'service__product', 'user').all()
    serializer_class = ReturnProductSerializer
    permission_codes = 'return_product_list'

    def get_queryset(self):
        qs = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            qs = qs.filter(date__range=(start_date, end_date))
        customer_name = self.request.query_params.get('customer_name')
        if customer_name:
            qs = qs.filter(customer__company_name__icontains=customer_name.strip())
        service_number = self.request.query_params.get('service_number')
        if service_number:
            qs = qs.filter(service__service_number__icontains=service_number.strip())
        return qs.order_by('-date')

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """售后返件数据导出"""
        import pandas as pd
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        data = [{
            '客户名称': r.customer.company_name if r.customer else '',
            '维修编号': r.service.service_number if r.service else '',
            '产品名称': r.service.productcategory.name if r.service and r.service.productcategory else '',
            '产品型号': r.service.product.model if r.service and r.service.product else '',
            '发货人': r.user.username if r.user else '',
            '发货时间': r.date,
        } for r in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'return_product_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

    @action(detail=False, methods=['get'], url_path='customers')
    def customers(self, request):
        """获取有已维修待返件的客户列表（warranty_end=2, return_status=1）"""
        query = request.query_params.get('q', '').strip()
        customers = models.Customer.objects.filter(
            Exists(models.Service.objects.filter(
                customer=OuterRef('pk'), is_delete=False, warranty_end=2, return_status=1)))
        if query:
            customers = customers.filter(company_name__icontains=query)
        customers = customers.order_by('company_name')[:DROPDOWN_SEARCH_LIMIT]
        return Response([{'id': c.id, 'company_name': c.company_name} for c in customers])

    @action(detail=False, methods=['get'], url_path='services')
    def services(self, request):
        """获取指定客户待返件的服务"""
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response([])
        services = models.Service.objects.filter(
            Q(customer_id=customer_id) & Q(is_delete=False) & Q(warranty_end=2) & Q(return_status=1)
        ).values('id', 'service_number', 'productcategory__name', 'product__model')
        return Response(list(services))

    @action(detail=False, methods=['post'], url_path='batch')
    def batch_create(self, request):
        """批量返件登记：一次为多个已维修产品创建返件记录。"""
        data = request.data
        customer_id = data.get('customer')
        return_date = data.get('date')
        service_ids = data.get('service_ids') or []
        if not customer_id:
            return Response({'detail': '请选择客户名称'}, status=400)
        if not any(service_ids):
            return Response({'detail': '该项目暂无可返件产品'}, status=400)
        if not return_date:
            return Response({'detail': '请选择返件日期'}, status=400)

        try:
            user = request.user
            user_id = user.id
        except Exception:
            user_id = None

        created = 0
        for service_id in service_ids:
            service = models.Service.objects.filter(id=service_id, is_delete=False).first()
            if service is None:
                continue
            models.ReturnProduct.objects.create(
                customer_id=customer_id,
                service=service,
                date=return_date,
                user_id=user_id,
            )
            service.return_status = 2
            service.save(update_fields=['return_status'])
            # 从售后流转转来的板子，返件即代表维修结束
            complete_archive_repair(service, getattr(request, 'user', None))
            created += 1
        if not created:
            return Response({'detail': '未成功创建返件记录'}, status=400)
        return Response({'created': created})

    def create(self, request, *args, **kwargs):
        data = request.data
        try:
            user = request.user
            data['user'] = user.id
        except Exception:
            pass
        instance = super().create(request, *args, **kwargs)
        service_id = request.data.get('service')
        if service_id:
            models.Service.objects.filter(pk=service_id).update(return_status=2)
            service = models.Service.objects.filter(pk=service_id).first()
            if service is not None:
                complete_archive_repair(service, getattr(request, 'user', None))
        return instance

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        service_id = instance.service_id
        result = super().destroy(request, *args, **kwargs)
        if not models.ReturnProduct.objects.filter(service_id=service_id, is_delete=False).exists():
            models.Service.objects.filter(pk=service_id).update(return_status=1)
            service = models.Service.objects.filter(pk=service_id).first()
            if service is not None:
                reopen_archive_repair(service, getattr(request, 'user', None))
        return result

    filter_backends = [filters.SearchFilter]
    search_fields = ['service__service_number', 'customer__company_name']
