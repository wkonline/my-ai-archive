import pandas as pd
from django.shortcuts import render, redirect,HttpResponse
from cono.tools.form import CustomerModelForm,ContractModelForm,CollectionModelForm,PlanModelForm,InvoiceModelForm
from cono import models

def upload_excel(request):
    pass
    # file_path= "D:/data/customer.xlsx"
    # df = pd.read_excel(file_path)
    # company_saler_dict ={s.name: s for s in models.User.objects.all()}
    # for index, row in df.iterrows():
    #     saler  = row['业务员']
    # #     # # collection_method = row['付款方式'] if pd.notna(row['付款方式']) else 1
    #     data = {
    #         'company_name':row['名称'],
    #         'contact_person': row['联系人']if pd.notna(row['联系人']) else 'Unknown',
    #         'phone' : row['电话'] if pd.notna(row['电话']) else 'Unknown',
    #         'address':row['地址']if pd.notna(row['地址']) else 'Unknown',
    #         'saler' : company_saler_dict[saler]
    #     }
    #     form = CustomerModelForm(data)
    #     if form.is_valid():
    #         form.save()
    # # return HttpResponse("上传成功")
    # file_path= "D:/data/customer.xlsx"
    # df = pd.read_excel(file_path)
    # for index, row in df.iterrows():
    #     data = {
    #         'company_name':row['company_name'],
    #         'contact_person': row['contact_person'],
    #         'phone': row['phone'],
    #         'address':row['address'],
    #         'saler_id':row['saler_id']
    #     }
    #     form = CustomerModelForm(data)
    #     if form.is_valid():
    #         form.save()
    # return HttpResponse("上传成功")


    # file_path= "D:/MyXiangMu/data/service.xlsx"
    # df = pd.read_excel(file_path)
    # for index, row in df.iterrows():#客户名称	物料名称	规格型号	维修编号	电路板编号	接收时间
    #     customer=row['客户名称']
    #     productcategory=row['物料名称']
    #     product=row['规格型号']
    #     service_number=row['维修编号']
    #     product_number=row['电路板编号']
    #     receive_date=row['接收时间']
    #     customer,created = models.Customer.objects.get_or_create(company_name=customer)
    #     productcategory,created = models.ProductCategory.objects.get_or_create(name=productcategory)
    #     product,created = models.Product.objects.get_or_create(model=product)
    #
    #     service = models.Service.objects.create(
    #         customer=customer,
    #         product=product,
    #         productcategory=productcategory,
    #         product_number=product_number,
    #         receive_date=receive_date,
    #         service_number=service_number,
    #         warranty=1,
    #         warranty_end=2
    #     )
    # return HttpResponse("上传成功")


    # file_path= "D:/MyXiangMu/data/hetong2024.xlsx"
    # df = pd.read_excel(file_path)
    # for index, row in df.iterrows():#购买方	数量	总价	合同日期	合同编号
    #     customer=row['购买方']
    #     print(customer)
    #     quantity=row['数量']
    #     total_price=row['总价']
    #     contract_number=row['合同编号']
    #     date=row['合同日期']
    #     customer,created = models.Customer.objects.get_or_create(company_name=str(customer))
    #     print(customer)
    #     service = models.Contract.objects.create(
    #         contract_number=contract_number,
    #         date=date,
    #         customer=customer,
    #         total_price=total_price,
    #         quantity=quantity
    #     )
    # return HttpResponse("上传成功")

    # file_path= "D:/MyXiangMu/data_2024/contract_data.xlsx"
    # df = pd.read_excel(file_path)
    # company_dict = {s.company_name : s for s in models.Customer.objects.all()}
    # for index, row in df.iterrows():
    #     customer=row['购买方'],
    #     customer = customer[0]
    #     print(row['数量'])
    #     print(type(row['总价']))
    #     data = {
    #         'date':row['合同日期'],
    #         'quantity' : row['数量'],
    #         'total_price' : row['总价'],
    #         'contract_number' : row['合同编号'],
    #     }
    #     # 验证合同编号是否重复
    #     # if models.Contract.objects.filter(contract_number=row['合同编号']).exists():
    #     #     return HttpResponse("合同编号%s重复"%row['合同编号'])
    #     form =ContractModelForm(data)
    #     if form.is_valid():
    #         form.instance.customer = company_dict[customer]
    #         form.save()
    # return HttpResponse("上传成功")


    # file_path= "D:/MyXiangMu/contract_data_202409272.xlsx"
    # df = pd.read_excel(file_path)
    # company_dict = {s.company_name : s for s in models.Customer.objects.all()}
    # contract_dict = {s.contract_number : s for s in models.Contract.objects.all()}
    # for index, row in df.iterrows():
    #     customer=row['客户名称'],
    #     customer = customer[0]
    #     contract =row['合同号码'],
    #     contract = contract[0]
    #     print(contract,customer)
    #     data = {
    #         'date':row['回款日期'],
    #         'amount' : row['回款金额'],
    #         'collection_method':1
    #     }
    #     #验证合同编号是否重复
    #     # if models.Contract.objects.filter(contract_number=row['合同编号']).exists():
    #     #     return HttpResponse("合同编号%s重复"%row['合同编号'])
    #     form =CollectionModelForm(data)
    #     if form.is_valid():
    #         form.instance.contract = contract_dict[contract]
    #         form.instance.customer = company_dict[customer]
    #         form.save()
    # return HttpResponse("上传成功")
    # objects_list = [
    #     # CNI100PD50CL02
    #     # CNI100PD50CL03
    #     # CNI200PD50CL02
    #     # CNI200PD20PH15
    #     # CNI250PD20PH09
    #     # CNI2-20PD50CL04
    #     # CNI400PD20PH05
    #     # CNI150PD100PH05
    #     # CNI80SD20IR03
    #     # IP120KW*1N
    #     # CNI300SD4PP01
    #     # CNI300PD20PH08
    #     # CNI250PD20PH16
    #     # CNI250PD20PH01
    #     # CNI300PD30PH01
    #     # CNI10-50PD50CL04
    #     # CNI250PD50CH04
    #     # CNI75PD20CC02
    #     # CNI80SD20IR02
    #     # CNI2-20PD50CL01
    #     # CNI200PD50PL01
    #     # CNI400PD50CL03
    #     # CNI400PD20PH13
    #     # CNI120PD20CC01
    #     # CNI80SD10PP01
    #     # CNI100PD50CL07
    #     # CNI100PD50CL08
    #     # CNI200PD50CL07
    #      models.Product(productcategory_id=10, model='CNI100PD50CL02',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI100PD50CL03',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI200PD50CL03',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI200PD20PH15',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI250PD20PH09',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI2-20PD50CL04',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI400PD20PH05',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI150PD100PH05',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI80SD20IR03',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='IP120KW*1N',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI300SD4PP01',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI300PD20PH08',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI250PD20PH16',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI250PD20PH01',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI300PD30PH01',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI10-50PD50CL04',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI250PD50CH04',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI75PD20CC02',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI80SD20IR02',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI2-20PD50CL01',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI200PD50PL01',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI400PD50CL03',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI400PD20PH13',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI120PD20CC01',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI80SD10PP01',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI100PD50CL07',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI100PD50CL08',warehouse_id=2),
    #      models.Product(productcategory_id=10, model='CNI200PD50CL07',warehouse_id=2),
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    # ]
    # models.Product.objects.bulk_create(objects_list)


    # file_path = "D:/MyXiangMu/data/plan_data_20240927.xlsx"
    # df = pd.read_excel(file_path)
    # contract_dict = {s.contract_number: s for s in models.Contract.objects.all()}
    # product_dict = {s.model: s for s in models.Product.objects.all()}
    # productcategory_dict = {s.name: s for s in models.ProductCategory.objects.all()}
    # for index, row in df.iterrows():
    #     contract = row['合同编号'],
    #     contract = contract[0]
    #     product = row['规格型号'],
    #     product = product[0]
    #     productcategory=row['产品名称'],
    #     productcategory = productcategory[0]
    #     print(contract,product)
    #     data = {
    #         'quantity': row['数量'],
    #         'unit':1,
    #         'configuration': row['详细配置'],
    #         'effective_date': row['合同生效日期'],
    #         'delivery_date': row['合同交货日期'],
    #     }
    #     # 验证合同编号是否重复
    #     # if models.Contract.objects.filter(contract_number=row['合同编号']).exists():
    #     #     return HttpResponse("合同编号%s重复"%row['合同编号'])
    #     form = PlanModelForm(data)
    #     if form.is_valid():
    #         form.instance.production_man_id=17
    #         form.instance.contract = contract_dict[contract]
    #         form.instance.productcategory = productcategory_dict[productcategory]
    #         form.instance.product = product_dict[product]
    #         form.save()
    # return HttpResponse("上传成功")

    # file_path= "D:/MyXiangMu/data/fapiao.xlsx"
    # df = pd.read_excel(file_path)
    # company_dict = {s.company_name : s for s in models.Customer.objects.all()}
    # contract_dict = {s.contract_number : s for s in models.Contract.objects.all()}
    # for index, row in df.iterrows():
    #     customer=row['购货单位'],
    #     customer = customer[0]
    #     contract =row['订单单号'],
    #     contract = contract[0]
    #     print(contract,customer)
    #     data = {
    #         'date':row['日期'],
    #         'amount' : row['开票金额'],
    #         'invoice_number':row['发票号码'],
    #     }
    #     # if models.Invoice.objects.filter(invoice_number=row['发票号码']).exists():
    #     #     print("发票%s重复" % row['发票号码'])
    #     form =InvoiceModelForm(data)
    #     if form.is_valid():
    #         form.instance.contract = contract_dict[contract]
    #         form.instance.customer = company_dict[customer]
    #         form.instance.invoice_man_id=17
    #         form.save()
    # return HttpResponse("上传成功")
