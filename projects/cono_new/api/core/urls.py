from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.core.views.auth import LoginView
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
    path('home/', HomeView.as_view(), name='api_home'),
    path('', include(router.urls)),
]
