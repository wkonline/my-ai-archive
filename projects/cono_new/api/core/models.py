"""
新版后端模型：字段与表名和老版 cono/models.py 100% 一致。
本地开发使用 SQLite 测试库；上线时 USE_MYSQL=1 直连老版 cono 库（同一份数据）。
"""
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
import datetime
import os
import re

TEMP_CONTRACT_NUMBER = 'No_Order_Stocking'


class ModelBase(models.Model):
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    class Meta:
        abstract = True


class Department(models.Model):
    title = models.CharField(verbose_name="部门", max_length=16, unique=True, db_index=True)
    description = models.CharField(verbose_name="部门描述", max_length=128, blank=True, null=True)

    class Meta:
        db_table = 'department'
        ordering = ['title']

    def __str__(self):
        return self.title


class User(models.Model):
    ROLE_CHOICES = (
        ('admin', "管理员"),
        ('saler', "业务员"),
        ('servicer', "客户经理"),
        ('upkeeper', "售后服务"),
        ('finance', "财务经理"),
    )
    role = models.CharField(verbose_name="角色", max_length=12, choices=ROLE_CHOICES, default="servicer")
    username = models.CharField(verbose_name="用户名", max_length=16)
    password = models.CharField(verbose_name="密码", max_length=128)
    GENDER_CHOICES = ((1, "男"), (2, "女"))
    gender = models.IntegerField(verbose_name="性别", choices=GENDER_CHOICES, default=1)
    id_number = models.CharField(verbose_name="身份证号", max_length=18, unique=True)
    phone = models.CharField(verbose_name="手机", max_length=11)
    address = models.CharField(verbose_name="地址", max_length=128)
    department = models.ForeignKey(to=Department, verbose_name="部门", on_delete=models.PROTECT)
    create_date = models.DateField(verbose_name="入职时间")

    class Meta:
        db_table = 'user'

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_username(self):
        return self.username

    def __str__(self):
        return self.username


class Customer(ModelBase):
    company_name = models.CharField(verbose_name="客户名称", max_length=64)
    contact_person = models.CharField(verbose_name="联系人", max_length=16, blank=True, null=True)
    phone = models.CharField(verbose_name="电话", max_length=20, blank=True, null=True)
    address = models.CharField(verbose_name="地址", max_length=128, blank=True, null=True)
    saler = models.ForeignKey(verbose_name="业务员", to="User", default=1, on_delete=models.PROTECT)

    class Meta:
        db_table = 'customer'

    def __str__(self):
        return self.company_name


class Warehouse(models.Model):
    name = models.CharField(max_length=32, verbose_name="仓库名称")
    address = models.CharField(max_length=128, verbose_name="仓库地址")

    class Meta:
        db_table = 'warehouse'

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(verbose_name='产品名称', max_length=32)
    description = models.CharField(verbose_name='产品描述', max_length=64, blank=True, null=True)

    class Meta:
        db_table = 'productcategory'

    def __str__(self):
        return self.name


class Product(models.Model):
    productcategory = models.ForeignKey(verbose_name="产品名称", to="ProductCategory", on_delete=models.PROTECT)
    model = models.CharField(verbose_name='产品型号', max_length=32, unique=True)
    warehouse = models.ForeignKey(verbose_name="属于的仓库", to="Warehouse", on_delete=models.PROTECT)
    description = models.CharField(verbose_name='产品描述', max_length=128, blank=True, null=True)

    class Meta:
        db_table = 'product'

    def __str__(self):
        return self.model


def contract_attachment_path(instance, filename):
    year = instance.date.year if instance.date else datetime.date.today().year
    customer_name = ''
    if instance.customer_id:
        customer = Customer.objects.filter(id=instance.customer_id).first()
        if customer:
            customer_name = customer.company_name
    base, ext = os.path.splitext(filename)
    fname = "{}-{}-{}".format(instance.order_number, instance.contract_number, customer_name)
    fname = re.sub(r'[\\/:*?"<>|\s]+', '_', fname).strip('_') or "contract"
    return "contract/{}/{}{}".format(year, fname, ext or "")


class Contract(ModelBase):
    order_number = models.IntegerField(verbose_name="合同号", validators=[MinValueValidator(1)], default=1)
    date = models.DateField(verbose_name="日期")
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT)
    contract_number = models.CharField(verbose_name="合同号码", max_length=20, unique=True)
    quantity = models.IntegerField(verbose_name="合同数量", default=1)
    total_price = models.DecimalField(verbose_name="合同金额", max_digits=10, decimal_places=2, default=0.00)
    payment_completed = models.BooleanField(default=False, verbose_name="货款完结状态")
    invoice_completed = models.BooleanField(default=False, verbose_name="发票完结状态")
    attachment = models.FileField(upload_to=contract_attachment_path, verbose_name="合同附件", blank=True, null=True)
    remark = models.TextField(verbose_name="备注", blank=True, null=True)

    class Meta:
        db_table = 'contract'

    def __str__(self):
        return str(self.contract_number)

    def total_collection(self):
        return self.collection_set.all().aggregate(Sum('amount'))['amount__sum'] or 0

    def total_invoice(self):
        return self.invoice_set.all().aggregate(Sum('amount'))['amount__sum'] or 0

    def collection_ratio(self):
        total_paid = self.total_collection()
        if self.total_price == 0:
            return 0
        return (total_paid / self.total_price) * 100

    def invoice_ratio(self):
        total_invoiced = self.total_invoice()
        if self.total_price == 0:
            return 0
        return (total_invoiced / self.total_price) * 100

    def outstanding_balance(self):
        return self.total_price - self.total_collection()

    def update_payment_completed_status(self):
        total_paid = Collection.objects.filter(contract=self).aggregate(Sum('amount'))['amount__sum'] or 0
        self.payment_completed = total_paid >= self.total_price
        self.save()

    def update_invoice_completed_status(self):
        total_paid = Invoice.objects.filter(contract=self).aggregate(Sum('amount'))['amount__sum'] or 0
        self.invoice_completed = total_paid >= self.total_price
        self.save()


class Contract_Product(models.Model):
    contract = models.ForeignKey(verbose_name="合同编号", to="Contract", on_delete=models.PROTECT)
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT, default=1)
    category = models.ForeignKey(verbose_name="产品名称", to="ProductCategory", on_delete=models.PROTECT)
    product = models.ForeignKey(verbose_name="产品型号", to="Product", on_delete=models.PROTECT)
    contract_type = models.CharField(
        verbose_name="合同类型", max_length=16,
        choices=(("sale", "销售服务"), ("repair", "维修服务")), default="sale")
    quantity = models.IntegerField(verbose_name="数量", validators=[MinValueValidator(1)])
    price = models.DecimalField(verbose_name="产品单价", max_digits=10, decimal_places=2)
    total_price = models.DecimalField(verbose_name="产品总价", max_digits=10, decimal_places=2)
    description = models.CharField(verbose_name="备注", max_length=128, blank=True, null=True)

    class Meta:
        db_table = 'contract_product'

    def __str__(self):
        return str(self.contract)


class Collection(ModelBase):
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT)
    contract = models.ForeignKey(verbose_name="合同编号", to="Contract", on_delete=models.PROTECT)
    date = models.DateField(verbose_name="回款日期")
    amount = models.DecimalField(verbose_name="回款金额", max_digits=10, decimal_places=2)
    collection_method_choices = (
        (1, "电汇"), (2, "银承"), (3, "现金"), (4, "万纳信"), (5, "迪链"))
    collection_method = models.IntegerField(verbose_name="回款方式", choices=collection_method_choices, default=1)

    class Meta:
        db_table = 'collection'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.contract.update_payment_completed_status()

    def __str__(self):
        return f"Collection {self.id} for Contract {self.contract.contract_number}"


class Invoice(ModelBase):
    date = models.DateField(verbose_name="日期")
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT)
    contract = models.ForeignKey(verbose_name="合同编号", to="Contract", on_delete=models.PROTECT)
    invoice_number = models.CharField(verbose_name="发票号码", max_length=20)
    amount = models.DecimalField(verbose_name="开票金额", max_digits=10, decimal_places=2)
    invoice_man = models.ForeignKey(verbose_name="开票人", to="User", on_delete=models.PROTECT)

    class Meta:
        db_table = 'invoice'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.contract.update_invoice_completed_status()

    def __str__(self):
        return f"Invoice {self.id} for Contract {self.contract.contract_number}"


class Service(ModelBase):
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT)
    productcategory = models.ForeignKey(verbose_name="产品名称", to="ProductCategory", on_delete=models.PROTECT)
    product = models.ForeignKey(verbose_name="产品型号", to="Product", on_delete=models.PROTECT)
    service_number = models.CharField(verbose_name="维修编号", max_length=20)
    product_number = models.CharField(verbose_name="产品编号", max_length=20, blank=True, null=True)
    WARRANTY_CHOICES = ((1, "质保外"), (2, "质保内"))
    warranty = models.IntegerField(verbose_name="质保状态", choices=WARRANTY_CHOICES, default=1)
    WARRANTY_END_CHOICES = ((1, "正在维修"), (2, "维修完成"))
    warranty_end = models.IntegerField(verbose_name="售后完结", choices=WARRANTY_END_CHOICES, default=1)
    RETURN_CHOICES = ((1, "未发货"), (2, "已发货"))
    return_status = models.IntegerField(verbose_name="返件状态", choices=RETURN_CHOICES, default=1)
    date = models.DateField(verbose_name="接收日期")
    repairman = models.ForeignKey(verbose_name="责任人", to="User", on_delete=models.PROTECT, default=17)
    description = models.CharField(verbose_name="备注", max_length=128, blank=True, null=True)

    class Meta:
        db_table = 'service'

    def __str__(self):
        return str(self.service_number)


class ServiceDetail(ModelBase):
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT, default=1)
    service = models.ForeignKey(verbose_name="维修编号", to="Service", on_delete=models.PROTECT)
    productcategory = models.ForeignKey(
        verbose_name="产品名称", to="ProductCategory", on_delete=models.PROTECT, blank=True, null=True)
    product = models.ForeignKey(
        verbose_name="产品型号", to="Product", on_delete=models.PROTECT, blank=True, null=True)
    repairman = models.ForeignKey(verbose_name="维修人", to="User", on_delete=models.PROTECT)
    fault_text = models.TextField(verbose_name="故障现象")
    fault_reason = models.TextField(verbose_name="故障原因")
    repair_method = models.TextField(verbose_name="维修方法")
    repair_date = models.DateField(verbose_name="维修完成时间")

    class Meta:
        db_table = 'service_detail'

    def __str__(self):
        return str(self.service)


class ReturnProduct(ModelBase):
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT)
    service = models.ForeignKey(verbose_name="维修编号", to="Service", on_delete=models.PROTECT)
    date = models.DateField(verbose_name="日期")
    user = models.ForeignKey(verbose_name="发货人", to="User", on_delete=models.PROTECT, default=17)

    class Meta:
        db_table = 'return_product'


class Plan(ModelBase):
    contract = models.ForeignKey(verbose_name="合同编号", to="Contract", on_delete=models.PROTECT)
    contract_reserve = models.CharField(verbose_name="备用编号", max_length=20, blank=True, null=True)
    productcategory = models.ForeignKey(verbose_name="产品名称", to="ProductCategory", on_delete=models.PROTECT)
    product = models.ForeignKey(verbose_name="产品型号", to="Product", on_delete=models.PROTECT)
    quantity = models.IntegerField(verbose_name="数量", validators=[MinValueValidator(1)])
    production_man = models.ForeignKey(verbose_name="制单人", to="User", on_delete=models.PROTECT, default=1)
    UNIT_CHOICES = ((1, "台"), (2, "套"), (3, "个"))
    unit = models.IntegerField(verbose_name="单位", choices=UNIT_CHOICES, default=1)
    configuration = models.TextField(verbose_name="详细配置信息")
    effective_date = models.DateField(verbose_name="生效日期")
    delivery_date = models.DateField(verbose_name="交货日期")
    STATUS_CHOICES = ((1, "待生产"), (2, "生产中"), (3, "已完成"))
    completed_status = models.IntegerField(verbose_name="任务单状态", choices=STATUS_CHOICES, default=1)
    completed = models.BooleanField(default=False, verbose_name="完结状态")

    class Meta:
        db_table = 'plan'

    @property
    def is_temp_plan(self):
        return self.contract.contract_number == TEMP_CONTRACT_NUMBER

    def __str__(self):
        return str(self.contract)


class ProductionTask(ModelBase):
    contract = models.ForeignKey(verbose_name="合同编号", to="Plan", on_delete=models.PROTECT)
    date = models.DateField(verbose_name="日期")
    productcategory = models.CharField(verbose_name="产品名称", max_length=32, blank=True, null=True)
    product = models.CharField(verbose_name="产品型号", max_length=32, blank=True, null=True)
    quantity = models.IntegerField(verbose_name="数量", blank=True, null=True)
    production_man = models.ForeignKey(verbose_name="负责人", to="User", on_delete=models.PROTECT, default=1)

    class Meta:
        db_table = 'production_task'


def contract_file_path(instance, filename):
    contract_number = instance.contract
    return f'{contract_number}/{filename}'


class ContractFile(ModelBase):
    contract = models.ForeignKey(verbose_name="合同编号", to="Plan", on_delete=models.PROTECT)
    electrical_drawings = models.FileField(upload_to=contract_file_path, verbose_name='电气原理图', blank=True, null=True)
    instruction = models.FileField(upload_to=contract_file_path, verbose_name='说明书', blank=True, null=True)
    packing_list = models.FileField(upload_to=contract_file_path, verbose_name='装箱清单', blank=True, null=True)
    mechanical_drawings = models.FileField(upload_to=contract_file_path, verbose_name='机械图纸', blank=True, null=True)
    other_file = models.FileField(upload_to=contract_file_path, verbose_name='其他文件', blank=True, null=True)

    class Meta:
        db_table = 'contractfile'


class ProductLabel(ModelBase):
    product = models.ForeignKey(verbose_name="型号", to="Product", on_delete=models.PROTECT)
    power = models.CharField(verbose_name="电源功率(kW)", max_length=20)
    frequency = models.CharField(verbose_name="电源频率(kHz)", max_length=20)
    sup_capacity = models.CharField(verbose_name="供电容量(kVA)", max_length=20)
    sup_voltage = models.CharField(verbose_name="供电电压(V)", max_length=20)
    sup_frequency = models.CharField(verbose_name="供电频率(Hz)", max_length=20)
    sup_current = models.CharField(verbose_name="供电电流(A)", max_length=20)
    max_in_temp = models.CharField(verbose_name="最高进水温度(°C)", max_length=20)
    max_pressure = models.CharField(verbose_name="最大压力(MPa)", max_length=20)
    min_flow = models.CharField(verbose_name="最小流量(L/min)", max_length=20)
    min_pressure = models.CharField(verbose_name="最小压力(MPa)", max_length=20)

    class Meta:
        db_table = 'productlabel'


class ProductDelivery(ModelBase):
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT, default=1)
    date = models.DateField(verbose_name="发货日期")
    contract = models.ForeignKey(verbose_name="合同编号", to="Plan", on_delete=models.PROTECT)
    productcategory = models.CharField(verbose_name="产品名称", max_length=32, blank=True, null=True)
    product = models.CharField(verbose_name="产品型号", max_length=32, blank=True, null=True)
    quantity = models.IntegerField(verbose_name="数量", blank=True, null=True)
    delivery_man = models.ForeignKey(verbose_name="发货人", to="User", on_delete=models.PROTECT)

    class Meta:
        db_table = 'product_delivery'


class Admin(models.Model):
    username = models.CharField(verbose_name="用户名", max_length=32)
    password = models.CharField(verbose_name="密码", max_length=64)

    def __str__(self):
        return self.username


class MyCompany(models.Model):
    company_name = models.CharField(verbose_name="公司名称", max_length=32)
    company_tax_number = models.CharField(verbose_name="公司税号", max_length=32)
    company_bank_account = models.CharField(verbose_name="银行账号", max_length=32)
    company_bank = models.CharField(verbose_name="开户行", max_length=32)
    company_bank_code = models.CharField(verbose_name="银行行号", max_length=32)
    company_address = models.CharField(verbose_name="公司地址", max_length=128)
    company_phone = models.CharField(verbose_name="公司电话", max_length=32)
    company_fax = models.CharField(verbose_name="公司传真", max_length=32)
    company_email = models.CharField(verbose_name="公司邮箱", max_length=32)
    company_website = models.CharField(verbose_name="公司网址", max_length=32)

    class Meta:
        db_table = 'cono_mycompany'
class UserLog(models.Model):
    user = models.ForeignKey(verbose_name="用户", to="User", on_delete=models.PROTECT)
    action = models.CharField(max_length=255)
    ip = models.CharField(max_length=64, default="192.168.1.1")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.action}'

    class Meta:
        db_table = 'cono_userlog'
class AuthRole(models.Model):
    key = models.CharField(verbose_name="角色标识", max_length=32, unique=True)
    name = models.CharField(verbose_name="角色名称", max_length=64)
    permissions = models.JSONField(verbose_name="权限编码", default=list, blank=True)
    menus = models.JSONField(verbose_name="顶部栏目", default=list, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auth_role'
        ordering = ['key']

    def __str__(self):
        return self.name


class AuthUserProfile(models.Model):
    user = models.OneToOneField(User, verbose_name="用户", on_delete=models.CASCADE, related_name="auth_profile")
    extra_permissions = models.JSONField(default=list, blank=True)
    denied_permissions = models.JSONField(default=list, blank=True)
    menus = models.JSONField(default=list, blank=True)
    menu_customize = models.BooleanField(default=False)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auth_user_profile'

    def __str__(self):
        return self.user.username


class AccountVault(ModelBase):
    category = models.CharField(verbose_name="分类", max_length=32, blank=True, null=True)
    name = models.CharField(verbose_name="平台名称", max_length=64)
    url = models.CharField(verbose_name="网址", max_length=255, blank=True, null=True)
    account = models.CharField(verbose_name="登录账号", max_length=128, blank=True, null=True)
    password = models.CharField(verbose_name="登录密码", max_length=128, blank=True, null=True)
    remark = models.TextField(verbose_name="备注", blank=True, null=True)

    class Meta:
        db_table = 'account_vault'
        ordering = ['-id']

    def __str__(self):
        return self.name
