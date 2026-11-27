from django.contrib import admin
from django.urls import path, re_path
from django.views.static import serve
from cono.views import contract,index,department,user,customer,collection,\
    warehouse,product,productcategory,upload,service,category,servicedetail,\
    account,plan,upload_file,productlabel,delivery,invoice,admin,chart,return_product,task,database,ajax_data,company,log
from cono.views import auth_manage
from cono.views import account_vault
from cono.views import dify_integration
from cono.views import announcement
from django.conf import settings

urlpatterns = [
    # 静态文件
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root':settings.MEDIA_ROOT},name='media'),

    # 管理后台
    # path('admin/', admin.site.urls),
    # 首页
    path('', index.home, name='home'),
    # 用户注册
    path('register/', account.register,name='register'),
    #ajax 数据
    path('ajax/search-companys/', contract.search_companys, name='search_companys'),
    path('ajax/check-contract-number/', contract.check_contract_number, name='check_contract_number'),
    path('ajax/get-contract_amount/', ajax_data.contract_amount, name='get_contract_amount'),
    path('ajax/get_productcategory_product/', ajax_data.productcategory_product, name='get_productcategory_product'),
    path('ajax/get_category_list/', ajax_data.get_category_list, name='get_category_list'),
    # 上传文件到数据库
    path('upload/', upload.upload_excel, name='upload_excel'),

    # 部门管理
    path('department/list/', department.department_list, name='department_list'),
    path('department/add/', department.department_add, name='department_add'),
    path('department/<int:nid>/edit/', department.department_edit, name='department_edit'),
    path('department/delete/', department.department_delete, name='department_delete'),

    # 合同管理
    path('contract/list/', contract.contract_list, name='contract_list'),
    path('contract/create/', contract.contract_create, name='contract_create'),
    path('contract/<int:nid>/edit/', contract.contract_edit, name='contract_edit'),
    path('contract/<int:nid>/delete/', contract.contract_delete, name='contract_delete'),
    path('contract/detail/<int:nid>/', contract.contract_product, name='contract_product'),
    path('contract/product_list/', contract.product_list, name='contract_product_list'),
    path('contract/download_excel/', contract.contract_download_excel, name='contract_download_excel'),
    path('contract/multi/', contract.contract_product_download_excel, name='contract_product_download_excel'),
    path('contract_product/multi/', contract.contract_product_multi, name='contract_product_multi'),

    #任务单
    path('task/list/', task.task_list, name='task_list'),
    path('task/add/', task.task_add, name='task_add'),
    path('task/<int:nid>/edit/', task.task_edit, name='task_edit'),
    path('task/delete/', task.task_delete, name='task_delete'),

    # 用户管理
    path('user/list/', user.user_list, name='user_list'),
    path('user/add/', user.user_add, name='user_add'),
    path('user/<int:nid>/edit/', user.user_edit, name='user_edit'),
    path('user/<int:nid>/reset/', user.user_reset, name='user_reset'),
    path('user/delete/', user.user_delete, name='user_delete'),
    # 个人信息
    path('user/profile/', user.user_profile, name='user_profile'),
    path('user/profile/edit/', user.user_profile_edit, name='user_profile_edit'),
    path('user/profile/password/', user.user_change_password, name='user_change_password'),

    # 客户管理
    path('customer/list/', customer.customer_list, name='customer_list'),
    path('customer/add/', customer.customer_add, name='customer_add'),
    path('customer/<int:nid>/edit/', customer.customer_edit, name='customer_edit'),
    path('customer/delete/', customer.customer_delete, name='customer_delete'),

    # 合同回款管理
    path('collection/list/', collection.collection_list, name='collection_list'),
    path('collection/create/', collection.collection_create, name='collection_create'),
    path('collection/add/', collection.collection_add, name='collection_add'),
    path('collection/<int:nid>/edit/', collection.collection_edit, name='collection_edit'),
    path('collection/delete/', collection.collection_delete, name='collection_delete'),
    path('collection/download_excel/', collection.collection_download_excel, name='collection_download_excel'),

    #登录
    path('login/', account.login),
    path('logout/', account.logout),
    path('image/code/', account.image_code,name = 'image_code'),

    # 仓库
    path('warehouse/list/', warehouse.warehouse_list, name='warehouse_list'),
    path('warehouse/add/', warehouse.warehouse_add, name='warehouse_add'),
    path('warehouse/delete/', warehouse.warehouse_delete, name='warehouse_delete'),
    path('warehouse/<int:nid>/edit/', warehouse.warehouse_edit, name='warehouse_edit'),

    # 产品分类
    path('productcategory/list/', productcategory.productcategory_list, name='productcategory_list'),
    path('productcategory/add/', productcategory.productcategory_add, name='productcategory_add'),
    path('productcategory/delete/', productcategory.productcategory_delete, name='productcategory_delete'),
    path('productcategory/<int:nid>/edit/', productcategory.productcategory_edit, name='productcategory_edit'),
    path('productcategory/multi/', productcategory.productcategory_multi, name='productcategory_multi'),
    # 产品
    path('product/list/', product.product_list, name='product_list'),
    path('product/add/', product.product_add, name='product_add'),
    path('product/delete/', product.product_delete, name='product_delete'),
    path('product/<int:nid>/edit/', product.product_edit, name='product_edit'),
    path('ajax/search-warehouses/', product.search_warehouses, name='search_warehouses'),

    # 售后服务
    path('service/list/', service.service_list, name='service_list'),
    path('service/add/', service.service_add, name='service_add'),
    path('service/copy/<int:nid>/', service.service_copy, name='service_copy'),
    path('service/delete/', service.service_delete, name='service_delete'),
    path('service/<int:nid>/edit/', service.service_edit, name='service_edit'),
    path('service/download_excel/', service.service_download_excel, name='service_download_excel'),
    path('service/detail/<str:service_number>/', service.service_detail, name='service_detail'),
    # path('service/multi/', service.service_multi, name='service_multi'),


    # # 获取产品分类
    # path('category/list/', category.category_list, name='get_category_list'),

    # #通过分类id获取产品
    # path('products/<int:productcategory_id>/', category.load_products, name='load_products'),

    # 售后详情
    path('servicedetail/list/', servicedetail.servicedetail_list, name='servicedetail_list'),
    path('servicedetail/add/', servicedetail.servicedetail_add, name='servicedetail_add'),
    path('servicedetail/batch_add/', servicedetail.servicedetail_batch_add, name='servicedetail_batch_add'),
    path('servicedetail/knowledge/', servicedetail.servicedetail_knowledge, name='servicedetail_knowledge'),
    # path('servicedetail/create/', servicedetail.servicedetail_create, name='servicedetail_create'),
    path('servicedetail/download_excel/', servicedetail.servicedetail_download_excel, name='servicedetail_download_excel'),

    path('servicedetail/delete/', servicedetail.servicedetail_delete, name='servicedetail_delete'),
    path('servicedetail/<int:nid>/edit/', servicedetail.servicedetail_edit, name='servicedetail_edit'),
    path('ajax/get_servicedetail_services/', servicedetail.get_servicedetail_services, name='get_servicedetail_services'),
    path('ajax/get_product_model/', servicedetail.get_product_model, name='get_product_model'),

    # 生产计划
    path('plan/list/', plan.plan_list, name='plan_list'),
    path('plan/add/', plan.plan_add, name='plan_add'),
    path('ajax/get-plan-contract-products/', plan.plan_contract_products, name='plan_contract_products'),
    path('plan/delete/', plan.plan_delete, name='plan_delete'),
    path('plan/<int:nid>/edit/', plan.plan_edit, name='plan_edit'),
    path('plan/download_excel/', plan.plan_download_excel, name='plan_download_excel'),
    # path('plan/print/<int:nid>/', plan.print_plan, name='print_plan'),



    #合同文件
    path('contract_file/list/', upload_file.contract_file_list, name='contract_file_list'),
    path('contract_file/add/electrical/', upload_file.upload_electrical_file,name='electrical_file'),
    path('contract_file/add/mechanical/', upload_file.upload_mechanical_file, name='mechanical_file'),
    path('contract_file/add/bill/', upload_file.upload_bill_file, name='bill_file'),
    path('contract_file/<int:nid>/edit/', upload_file.edit_contract_file, name='edit_contract_file'),
    path('contract_file/<int:nid>/delete/', upload_file.delete_contract_file, name='delete_contract_file'),


    path('ajax/get-collection_contracts/', collection.get_collection_contracts, name='get_collection_contracts'),
    path('ajax/get_collection_customers/', collection.get_collection_customers, name='get_collection_customers'),

    #产品标牌
    path('productlabel/list/', productlabel.productlabel_list, name='productlabel_list'),
    path('productlabel/add/', productlabel.productlabel_add, name='productlabel_add'),
    path('productlabel/delete/', productlabel.productlabel_delete, name='productlabel_delete'),
    path('productlabel/<int:nid>/edit/', productlabel.productlabel_edit, name='productlabel_edit'),

    #发货信息
    path('delivery/list/',delivery.delivery_list,name='delivery_list'),
    path('delivery/add/',delivery.delivery_add,name='delivery_add'),
    path('delivery/delete/',delivery.delivery_delete,name='delivery_delete'),
    path('delivery/<int:nid>/edit/',delivery.delivery_edit,name='delivery_edit'),
    path('delivery/multi/', delivery.delivery_multi, name='delivery_multi'),
    path('delivery/download_excel/', delivery.delivery_download_excel, name='delivery_download_excel'),
    path('ajax/delivery-customer-info/', delivery.customer_info, name='delivery_customer_info'),



    path('invoice/list/',invoice.invoice_list,name='invoice_list'),
    path('invoice/add/',invoice.invoice_add,name='invoice_add'),
    path('invoice/create/',invoice.invoice_create,name='invoice_create'),
    path('invoice/delete/',invoice.invoice_delete,name='invoice_delete'),
    path('invoice/<int:nid>/edit/',invoice.invoice_edit,name='invoice_edit'),
    #批量上传
    path('invoice/multi/', invoice.invoice_multi, name='invoice_multi'),
    path('ajax/get-invoice_contracts/', invoice.get_invoice_contracts, name='get_invoice_contracts'),

    # 数据统计
    path('chart/list/', chart.chart_list, name='chart_list'),
    path('chart/bar/', chart.chart_bar, name='chart_bar'),
    path('chart/bar2/', chart.chart_bar2, name='chart_bar2'),
    path('chart/pie/', chart.chart_pie, name='chart_pie'),
    path('chart/line/', chart.chart_line , name='chart_line'),
    path('chart/highcharts/', chart.highcharts, name='highcharts'),

    # 售后返件
    path('return_product/list/', return_product.return_product_list, name='return_product_list'),
    path('return_product/add/', return_product.return_product_add, name='return_product_add'),
    path('return_product/batch_add/', return_product.return_product_batch_add, name='return_product_batch_add'),
    path('return_product/delete/', return_product.return_product_delete, name='return_product_delete'),
    path('return_product/<int:nid>/edit/', return_product.return_product_edit, name='return_product_edit'),
    path('ajax/get_return_product_services/', return_product.get_return_product_services,name='get_return_product_services'),
    path('ajax/get_return_product_model/', return_product.get_return_product_model, name='get_return_product_model'),


    path('database/backup/list/', database.backup_database, name='backup_database'),
    path('database/restore/list/', database.restore_database, name='restore_database'),


    #公司信息
    path('company/list/', company.company_show, name='company_show'),
    path('company/edit/<int:nid>/', company.company_edit, name='company_edit'),

    #操作日志
    path('log/list/', log.log_list, name='get_log'),

]


urlpatterns += [
    # 平台账号密码
    path('account_vault/list/', account_vault.account_vault_list, name='account_vault_list'),
    path('account_vault/add/', account_vault.account_vault_add, name='account_vault_add'),
    path('account_vault/<int:nid>/edit/', account_vault.account_vault_edit, name='account_vault_edit'),
    path('account_vault/<int:nid>/password/', account_vault.account_vault_password, name='account_vault_password'),
    path('account_vault/delete/', account_vault.account_vault_delete, name='account_vault_delete'),

    path('dify/search/', dify_integration.search, name='dify_search'),
    path('auth/role/list/', auth_manage.role_list, name='auth_role_list'),
    path('auth/role/add/', auth_manage.role_add, name='auth_role_add'),
    path('auth/role/<int:pk>/edit/', auth_manage.role_edit, name='auth_role_edit'),
    path('auth/role/<int:pk>/delete/', auth_manage.role_delete, name='auth_role_delete'),
    path('auth/user/<int:nid>/permission/', auth_manage.user_permission, name='auth_user_permission'),

    # 公告通知（与新版共用数据，供老版顶栏铃铛调用）
    path('ajax/announcement/list/', announcement.announcement_list, name='announcement_list'),
    path('ajax/announcement/<int:nid>/read/', announcement.announcement_read, name='announcement_read'),
    path('ajax/announcement/read-all/', announcement.announcement_read_all, name='announcement_read_all'),

    # 公告管理（老版页面）
    path('announcement/list/', announcement.announcement_manage_list, name='announcement_manage_list'),
    path('announcement/add/', announcement.announcement_add, name='announcement_add'),
    path('announcement/<int:nid>/edit/', announcement.announcement_edit, name='announcement_edit'),
    path('announcement/delete/', announcement.announcement_delete, name='announcement_delete'),
    path('announcement/attachment/upload/', announcement.announcement_attachment_upload,
         name='announcement_attachment_upload'),
    path('announcement/attachment/<uuid:token>/download/',
         announcement.announcement_attachment_download, name='announcement_attachment_download'),
    path('announcement/attachment/<uuid:token>/delete/', announcement.announcement_attachment_delete,
         name='announcement_attachment_delete'),
]


handler403 = index.page_permission_denied
handler404 = index.page_not_found
handler500 = index.pagindexter_error
