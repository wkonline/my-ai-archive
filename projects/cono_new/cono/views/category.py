from django.shortcuts import render
from cono import models
from django.http import JsonResponse


def category_list(request):
    # 从数据库中查询所有产品类别
    categorys = models.ProductCategory.objects.all()
    context = {'categorys': categorys}
    return render(request, 'category.html', context)

def load_products(request, productcategory_id):
    products = models.Product.objects.filter(productcategory_id=productcategory_id)
    products_list = [{'id': subcat.id, 'name': subcat.model} for subcat in products]
    return JsonResponse(products_list, safe=False)

