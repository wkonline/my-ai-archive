import pandas as pd
from django.db.models import Q, OuterRef, Exists, Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from cono import models
from cono.tools.pagination import Pagination
from cono.tools.form import CollectionModelForm
import datetime
from io import BytesIO

# 通过合同编号获取合同金额
def contract_amount(request):
    if request.method == "GET":
        contract_id = request.GET.get('contract')
        # 前端未选择合同时（占位选项 value=""）会带空参数请求，这里直接返回 0，
        # 避免用无效主键查询导致 500。
        if not contract_id:
            return JsonResponse({'contract_amount': 0})
        try:
            contract_id = int(contract_id)
        except (TypeError, ValueError):
            return JsonResponse({'contract_amount': 0, 'error': '合同参数无效'}, status=400)
        contract = models.Contract.objects.filter(pk=contract_id).first()
        if contract is None:
            return JsonResponse({'contract_amount': 0, 'error': '合同不存在'}, status=404)
        return JsonResponse({'contract_amount': contract.outstanding_balance()})

#通过产品名称获取产品型号
def productcategory_product(request):
    if request.method == "GET":
        productcategory_id = request.GET.get('productcategory_id')
        # 未选择产品名称时（表单空选项）返回空列表，避免无效主键导致 500。
        if not productcategory_id:
            return JsonResponse([], safe=False)
        try:
            productcategory_id = int(productcategory_id)
        except (TypeError, ValueError):
            return JsonResponse([], safe=False)
        product_list = models.Product.objects.filter(productcategory_id=productcategory_id).values('id', 'model').order_by('model')
        return JsonResponse(list(product_list), safe=False)

# 获取生产计划表的产品名称
def get_category_list(request):
    if request.method == "GET":
        productcategorys = models.ProductCategory.objects.filter(Q(pk=10)|Q(pk=20)|Q(pk=96)).values('id', 'name')
        return JsonResponse(list(productcategorys), safe=False)
