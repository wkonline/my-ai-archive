from rest_framework import serializers
from api.core import models


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Department
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.title', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = models.User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'required': False, 'allow_blank': True},
            'username': {'required': False},
            'id_number': {'required': False},
            'address': {'required': False, 'allow_blank': True},
            'phone': {'required': False, 'allow_blank': True},
        }

    def create(self, validated_data):
        from django.conf import settings
        import hashlib
        password = validated_data.pop('password', None) or '123456'
        obj = models.User(**validated_data)
        if password:
            obj.password = self._hash(password)
        obj.save()
        return obj

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.password = self._hash(password)
        instance.save()
        return instance

    @staticmethod
    def _hash(password):
        # 必须与老系统一致：md5(LEGACY_SECRET_KEY + 明文)，否则新系统建/改的账号
        # 在老系统登录不了，反之亦然（两边共用 user 表）。
        from django.conf import settings
        import hashlib
        obj = hashlib.md5(settings.LEGACY_SECRET_KEY.encode('utf-8'))
        obj.update(str(password).encode('utf-8'))
        return obj.hexdigest()


class CustomerSerializer(serializers.ModelSerializer):
    saler_name = serializers.CharField(source='saler.username', read_only=True)

    class Meta:
        model = models.Customer
        fields = '__all__'


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Warehouse
        fields = '__all__'


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductCategory
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='productcategory.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = models.Product
        fields = '__all__'


class ContractSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    saler_name = serializers.CharField(source='customer.saler.username', read_only=True)
    attachment = serializers.CharField(read_only=True)
    total_collection = serializers.SerializerMethodField()
    total_invoice = serializers.SerializerMethodField()
    payment_ratio = serializers.SerializerMethodField()
    invoice_ratio = serializers.SerializerMethodField()
    outstanding_balance = serializers.SerializerMethodField()

    class Meta:
        model = models.Contract
        fields = '__all__'

    def get_total_collection(self, obj):
        from decimal import Decimal
        return float(obj.total_collection() or 0)

    def get_total_invoice(self, obj):
        from decimal import Decimal
        return float(obj.total_invoice() or 0)

    def get_payment_ratio(self, obj):
        total = obj.total_collection()
        if not obj.total_price or obj.total_price == 0:
            return 0
        return int((float(total or 0) / float(obj.total_price)) * 100)

    def get_invoice_ratio(self, obj):
        total = obj.total_invoice()
        if not obj.total_price or obj.total_price == 0:
            return 0
        return int((float(total or 0) / float(obj.total_price)) * 100)

    def get_outstanding_balance(self, obj):
        return float(obj.outstanding_balance() or 0)


class ContractProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    product_model = serializers.CharField(source='product.model', read_only=True)
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    contract_date = serializers.DateField(source='contract.date', read_only=True)
    contract_order_number = serializers.IntegerField(source='contract.order_number', read_only=True)
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)

    class Meta:
        model = models.Contract_Product
        fields = '__all__'


class CollectionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    collection_method_display = serializers.CharField(source='get_collection_method_display', read_only=True)
    saler_name = serializers.CharField(source='customer.saler.username', read_only=True)
    contract_total_price = serializers.SerializerMethodField()
    contract_balance = serializers.SerializerMethodField()
    collection_ratio = serializers.SerializerMethodField()

    class Meta:
        model = models.Collection
        fields = '__all__'

    def get_contract_total_price(self, obj):
        return float(obj.contract.total_price or 0)

    def get_contract_balance(self, obj):
        return float(obj.contract.outstanding_balance() or 0)

    def get_collection_ratio(self, obj):
        return int(obj.contract.collection_ratio() or 0)


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    invoice_man_name = serializers.CharField(source='invoice_man.username', read_only=True)
    contract_total_price = serializers.SerializerMethodField()
    contract_invoice_ratio = serializers.SerializerMethodField()
    contract_balance = serializers.SerializerMethodField()

    class Meta:
        model = models.Invoice
        fields = '__all__'

    def get_contract_total_price(self, obj):
        return float(obj.contract.total_price or 0)

    def get_contract_invoice_ratio(self, obj):
        return int(obj.contract.invoice_ratio() or 0)

    def get_contract_balance(self, obj):
        return float(obj.contract.outstanding_balance() or 0)


class ServiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    productcategory_name = serializers.CharField(source='productcategory.name', read_only=True)
    product_model = serializers.CharField(source='product.model', read_only=True)
    repairman_name = serializers.CharField(source='repairman.username', read_only=True)
    warranty_display = serializers.CharField(source='get_warranty_display', read_only=True)
    warranty_end_display = serializers.CharField(source='get_warranty_end_display', read_only=True)
    return_status_display = serializers.CharField(source='get_return_status_display', read_only=True)

    class Meta:
        model = models.Service
        fields = '__all__'


class ServiceDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    service_number = serializers.CharField(source='service.service_number', read_only=True)
    productcategory_name = serializers.CharField(source='productcategory.name', read_only=True)
    product_model = serializers.CharField(source='product.model', read_only=True)
    repairman_name = serializers.CharField(source='repairman.username', read_only=True)
    product_number = serializers.CharField(source='service.product_number', read_only=True)
    warranty_display = serializers.CharField(source='service.get_warranty_display', read_only=True)
    service_date = serializers.DateField(source='service.date', read_only=True)

    class Meta:
        model = models.ServiceDetail
        fields = '__all__'


class ReturnProductSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    service_number = serializers.CharField(source='service.service_number', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    productcategory_name = serializers.CharField(source='service.productcategory.name', read_only=True)
    product_model = serializers.CharField(source='service.product.model', read_only=True)

    class Meta:
        model = models.ReturnProduct
        fields = '__all__'


class PlanSerializer(serializers.ModelSerializer):
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    customer_name = serializers.CharField(source='contract.customer.company_name', read_only=True)
    productcategory_name = serializers.CharField(source='productcategory.name', read_only=True)
    product_model = serializers.CharField(source='product.model', read_only=True)
    production_man_name = serializers.CharField(source='production_man.username', read_only=True)
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    completed_status_display = serializers.CharField(source='get_completed_status_display', read_only=True)
    is_temp_plan = serializers.SerializerMethodField()

    class Meta:
        model = models.Plan
        fields = '__all__'

    def get_is_temp_plan(self, obj):
        return obj.is_temp_plan


class ProductionTaskSerializer(serializers.ModelSerializer):
    production_man_name = serializers.CharField(source='production_man.username', read_only=True)
    plan_number = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    plan_quantity = serializers.SerializerMethodField()
    is_temp_plan = serializers.SerializerMethodField()

    class Meta:
        model = models.ProductionTask
        fields = '__all__'

    def get_plan_number(self, obj):
        plan = obj.contract
        if plan and plan.contract:
            if plan.is_temp_plan:
                return plan.contract_reserve or ''
            return plan.contract.contract_number
        return ''

    def get_customer_name(self, obj):
        plan = obj.contract
        if plan and plan.contract and plan.contract.customer:
            return plan.contract.customer.company_name
        return ''

    def get_plan_quantity(self, obj):
        return obj.contract.quantity if obj.contract else None

    def get_is_temp_plan(self, obj):
        return obj.contract.is_temp_plan if obj.contract else False


class ContractFileSerializer(serializers.ModelSerializer):
    plan_number = serializers.SerializerMethodField()
    productcategory_name = serializers.SerializerMethodField()
    product_model = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractFile
        fields = '__all__'

    def get_plan_number(self, obj):
        plan = obj.contract
        if plan:
            if plan.contract_reserve:
                return plan.contract_reserve
            if plan.contract:
                return plan.contract.contract_number
        return ''

    def get_productcategory_name(self, obj):
        plan = obj.contract
        if plan and plan.productcategory:
            return plan.productcategory.name
        return ''

    def get_product_model(self, obj):
        plan = obj.contract
        if plan and plan.product:
            return plan.product.model
        return ''

    def get_quantity(self, obj):
        return obj.contract.quantity if obj.contract else None


class ProductLabelSerializer(serializers.ModelSerializer):
    product_model = serializers.CharField(source='product.model', read_only=True)
    productcategory_name = serializers.SerializerMethodField()

    class Meta:
        model = models.ProductLabel
        fields = '__all__'

    def get_productcategory_name(self, obj):
        if obj.product and obj.product.productcategory:
            return obj.product.productcategory.name
        return ''


class ProductDeliverySerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    delivery_man_name = serializers.CharField(source='delivery_man.username', read_only=True)
    contract_number = serializers.SerializerMethodField()
    contact_person = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    class Meta:
        model = models.ProductDelivery
        fields = '__all__'

    def get_contract_number(self, obj):
        plan = obj.contract
        if plan:
            if plan.contract_reserve:
                return plan.contract_reserve
            if plan.contract:
                return plan.contract.contract_number
        return ''

    def get_contact_person(self, obj):
        return obj.customer.contact_person if obj.customer else ''

    def get_phone(self, obj):
        return obj.customer.phone if obj.customer else ''

    def get_address(self, obj):
        return obj.customer.address if obj.customer else ''


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MyCompany
        fields = '__all__'


class UserLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = models.UserLog
        fields = '__all__'


class AuthRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuthRole
        fields = '__all__'


class AccountVaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccountVault
        fields = '__all__'
