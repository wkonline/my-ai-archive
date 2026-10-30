import json
import os
import re

from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from cono import models


SEARCH_TOKEN = os.environ.get('DIFY_SEARCH_TOKEN', 'cono-dify-search-2026')


def _authorized(request):
    header = request.headers.get('Authorization', '')
    token = request.headers.get('X-Dify-Token', '')
    return header == 'Bearer ' + SEARCH_TOKEN or token == SEARCH_TOKEN


def _clean_row(row):
    result = {}
    for key, value in row.items():
        if hasattr(value, 'strftime'):
            result[key] = value.strftime('%Y-%m-%d')
        elif hasattr(value, 'isoformat'):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result


def _search_terms(query):
    """从自然语言问题中提取可用于数据库模糊检索的关键词。"""
    terms = []
    seen = set()

    def add(term):
        term = str(term or '').strip()
        if term and term not in seen:
            seen.add(term)
            terms.append(term)

    # 客户名称、产品名称尽量整段命中，避免整句自然语言无法匹配
    for name in models.Customer.objects.filter(is_delete=False).values_list('company_name', flat=True).distinct():
        if name and name in query:
            add(name)
    for name in models.ProductCategory.objects.values_list('name', flat=True).distinct():
        if name and name in query:
            add(name)

    # 合同号、产品型号、发票号通常由字母数字组成，可单独切出来检索
    for token in re.findall(r'[A-Za-z0-9][A-Za-z0-9._/-]{2,}', query):
        add(token)

    if not terms:
        add(query)
    return terms[:8]


def _match_terms(fields, terms):
    q = Q()
    for term in terms:
        for field in fields:
            q |= Q(**{f'{field}__icontains': term})
    return q


@csrf_exempt
def search(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    if not _authorized(request):
        return JsonResponse({'error': 'unauthorized'}, status=403)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)

    query = str(data.get('query', '')).strip()
    modules = data.get('modules') or ['contracts', 'contract_products', 'collections', 'invoices']
    if not query:
        return JsonResponse({'error': 'query is required'}, status=400)

    response = {'query': query}
    terms = _search_terms(query)
    if 'contracts' in modules:
        contracts = models.Contract.objects.filter(
            _match_terms(['contract_number', 'customer__company_name'], terms),
            is_delete=False,
        ).order_by('-date')[:8]
        response['contracts'] = [_clean_row(row) for row in contracts.values(
            'id', 'contract_number', 'customer__company_name', 'date', 'quantity',
            'total_price', 'payment_completed', 'invoice_completed'
        )]
    if 'contract_products' in modules:
        contract_products = models.Contract_Product.objects.filter(
            _match_terms(
                [
                    'contract__contract_number',
                    'contract__customer__company_name',
                    'customer__company_name',
                    'category__name',
                    'product__model',
                ],
                terms,
            )
        ).order_by('-id')[:8]
        response['contract_products'] = [_clean_row(row) for row in contract_products.values(
            'id', 'contract__contract_number', 'customer__company_name',
            'category__name', 'product__model', 'contract_type',
            'quantity', 'price', 'total_price'
        )]
    if 'customers' in modules:
        customers = models.Customer.objects.filter(
            _match_terms(['company_name', 'contact_person', 'phone'], terms),
            is_delete=False,
        ).order_by('company_name')[:8]
        response['customers'] = [_clean_row(row) for row in customers.values(
            'id', 'company_name', 'contact_person', 'phone', 'address', 'saler__username'
        )]
    if 'collections' in modules:
        collections = models.Collection.objects.filter(
            _match_terms(['customer__company_name', 'contract__contract_number'], terms),
            is_delete=False,
        ).order_by('-date')[:8]
        response['collections'] = [_clean_row(row) for row in collections.values(
            'id', 'customer__company_name', 'contract__contract_number', 'date',
            'amount', 'collection_method'
        )]
    if 'invoices' in modules:
        invoices = models.Invoice.objects.filter(
            _match_terms(
                ['customer__company_name', 'contract__contract_number', 'invoice_number'],
                terms,
            ),
            is_delete=False,
        ).order_by('-date')[:8]
        response['invoices'] = [_clean_row(row) for row in invoices.values(
            'id', 'customer__company_name', 'contract__contract_number', 'date',
            'invoice_number', 'amount', 'invoice_man__username'
        )]
    return JsonResponse(response, safe=False)
