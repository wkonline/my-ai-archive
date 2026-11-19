from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.core.views.auth import (
    LoginView, RegisterView, PublicDepartmentsView, ChangePasswordView,
)
from api.core.views.captcha_view import CreateCaptchaView
from api.core.views.home import HomeView
from api.core.views.basic import (
    DepartmentViewSet, UserViewSet, CustomerViewSet,
    WarehouseViewSet, ProductCategoryViewSet, ProductViewSet,
)
from api.core.views.business import (
    ContractViewSet, ContractProductViewSet,
    CollectionViewSet, InvoiceViewSet,
)
from api.core.views.service import (
    ServiceViewSet, ServiceDetailViewSet, ReturnProductViewSet,
)
from api.core.views.production import (
    PlanViewSet, ProductionTaskViewSet,
    ContractFileViewSet, ProductLabelViewSet, ProductDeliveryViewSet,
)
from api.core.views import backup as views
from api.core.views.system import (
    CompanyViewSet, UserLogViewSet, AuthRoleViewSet, AccountVaultViewSet,
)

router = DefaultRouter()
router.register('department', DepartmentViewSet)
router.register('user', UserViewSet)
router.register('customer', CustomerViewSet)
router.register('warehouse', WarehouseViewSet)
router.register('productcategory', ProductCategoryViewSet)
router.register('product', ProductViewSet)
router.register('contract', ContractViewSet)
router.register('contract-product', ContractProductViewSet)
router.register('collection', CollectionViewSet)
router.register('invoice', InvoiceViewSet)
router.register('service', ServiceViewSet)
router.register('servicedetail', ServiceDetailViewSet)
router.register('return-product', ReturnProductViewSet)
router.register('plan', PlanViewSet)
router.register('task', ProductionTaskViewSet)
router.register('contract-file', ContractFileViewSet)
router.register('product-label', ProductLabelViewSet)
router.register('delivery', ProductDeliveryViewSet)
router.register('company', CompanyViewSet)
router.register('log', UserLogViewSet)
router.register('auth-role', AuthRoleViewSet)
router.register('account-vault', AccountVaultViewSet)

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='api_login'),
    path('auth/register/', RegisterView.as_view(), name='api_register'),
    path('auth/departments/', PublicDepartmentsView.as_view(), name='api_public_departments'),
    path('auth/captcha/', CreateCaptchaView.as_view(), name='api_captcha'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='api_change_password'),
    path('home/', HomeView.as_view(), name='api_home'),
    path('backup/list/', views.backup_list, name='backup_list'),
    path('backup/create/', views.backup_create, name='backup_create'),
    path('backup/restore/', views.backup_restore, name='backup_restore'),
    path('backup/restore/status/', views.backup_restore_status, name='backup_restore_status'),
    path('backup/delete/', views.backup_delete, name='backup_delete'),
    path('', include(router.urls)),
]
