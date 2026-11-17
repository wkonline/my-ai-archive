from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, FloatField
import datetime
import os
import re

# 无合同临时计划使用的备用合同编号
TEMP_CONTRACT_NUMBER = 'No_Order_Stocking'


# 抽象模型基类
class ModelBase(models.Model):
    """
    抽象模型基类
    """
    #创建时间
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    #更新时间
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    #是否删除
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    class Meta:
        # 抽象模型
        abstract = True

    # def delete(self, using=None, keep_parents=False):
    #     """
    #     重写delete方法来实现虚拟删除
    #     """
    #     self.is_deleted = True
    #     self.save()
    #
    # def restore(self):
    #     """
    #     恢复被虚拟删除的记录
    #     """
    #     self.is_deleted = False
    #     self.save()

#部门表
class Department(models.Model):
    """ 部门表 """
    # 部门名称，假设每个部门名称都是唯一的
    title = models.CharField(verbose_name="部门", max_length=16, unique=True, db_index=True)
    # 部门描述，可以为空
    description = models.CharField(verbose_name="部门描述", max_length=128, blank=True, null=True)

    class Meta:
        # 定义数据库表名为'department'
        db_table = 'department'
        # 设置默认排序字段为标题
        ordering = ['title']
    def __str__(self):
        return self.title

#员工表
class User(models.Model):
    """ 员工表 """
    #角色
    ROLE_CHOICES = (
        ('admin', "管理员"),
        ('saler', "业务员"),
        ('servicer', "客户经理"),
        ('upkeeper', "售后服务"),
        ('finance', "财务经理"),
    )
    role = models.CharField(verbose_name="角色", max_length=12,choices=ROLE_CHOICES, default="servicer")
    # 员工姓名
    username = models.CharField(verbose_name="用户名",max_length=16)
    # 员工登录密码
    password = models.CharField(verbose_name="密码",max_length=128)
    # 性别
    GENDER_CHOICES = (
        (1, "男"),
        (2, "女"),
    )
    gender = models.IntegerField(verbose_name="性别", choices=GENDER_CHOICES,default=1)
    # 身份证号，假设为18位,唯一性
    id_number = models.CharField(verbose_name="身份证号",max_length=18, unique=True)
    # 手机
    phone = models.CharField(verbose_name="手机",max_length=11)
    # 地址
    address = models.CharField(verbose_name= "地址",max_length=128)
    # 关联到Department模型
    department = models.ForeignKey(to=Department,verbose_name="部门", on_delete=models.PROTECT)
    # 入职时间
    create_date = models.DateField(verbose_name="入职时间")

    class Meta:
        # 定义数据库表名为'user'
        db_table = 'user'
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        # 返回员工姓名
        return self.username

#客户表
class Customer(ModelBase):
    """ 客户表 """
    # 客户名称
    company_name = models.CharField(verbose_name="客户名称", max_length=64)
    # 联系人
    contact_person = models.CharField(verbose_name="联系人", max_length=16,blank=True, null=True)
    # 手机
    phone = models.CharField(verbose_name="电话", max_length=20,blank=True, null=True)
    # 地址
    address = models.CharField(verbose_name="地址", max_length=128,blank=True, null=True)
    # 业务员
    saler = models.ForeignKey(verbose_name="业务员", to="User", default=1, on_delete=models.PROTECT)

    class Meta:
        # 定义数据库表名为'customer'
        db_table = 'customer'
    def __str__(self):
        # 返回客户名称
        return self.company_name

#仓库
class Warehouse(models.Model):
    """ 仓库 """
    # 仓库名称
    name = models.CharField(max_length=32, verbose_name="仓库名称")
    # 仓库地址
    address = models.CharField(max_length=128,verbose_name="仓库地址")

    class Meta:
        # 定义数据库表名为'warehouse'
        db_table = 'warehouse'

    def __str__(self):
        return self.name

#产品名称
class ProductCategory(models.Model):
    """ 产品名称 """
    # 产品名称
    name = models.CharField(verbose_name='产品名称',max_length=32)
    # 产品描述
    description = models.CharField(verbose_name='产品描述',max_length=64,blank=True, null=True)

    class Meta:
        # 定义数据库表名为'productcategory'
        db_table = 'productcategory'
    def __str__(self):
        # 返回产品名称
        return self.name

#产品型号
class Product(models.Model):
    """ 产品型号 """
    # 产品名称
    productcategory = models.ForeignKey(verbose_name="产品名称", to="ProductCategory", on_delete=models.PROTECT)
    # 产品型号
    model = models.CharField(verbose_name='产品型号', max_length=32, unique=True)
    # 所属仓库
    warehouse = models.ForeignKey(verbose_name="属于的仓库", to="Warehouse", on_delete=models.PROTECT)
    #详细信息
    description = models.CharField(verbose_name='产品描述', max_length=128, blank=True, null=True)

    class Meta:
        # 定义数据库表名为'product'
        db_table = 'product'



    def __str__(self):
        return self.model

#合同附件上传路径：media/contract/<年份>/<序号>-<合同号>-<客户名称>.<扩展名>
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

#合同跟踪表
class Contract(ModelBase):
    """ 合同跟踪表 """
    #合同顺序号
    order_number = models.IntegerField(verbose_name="合同号",validators=[MinValueValidator(1)],default=1)
    # 合同日期
    date = models.DateField(verbose_name="日期")
    # 客户名称
    customer = models.ForeignKey(verbose_name="客户名称" ,to="Customer",on_delete=models.PROTECT)
    # 合同编号
    contract_number = models.CharField(verbose_name="合同号码",max_length=20, unique=True)
    # 合同数量
    quantity = models.IntegerField(verbose_name="合同数量",default=1)
    # 合同金额
    total_price = models.DecimalField(verbose_name="合同金额", max_digits=10, decimal_places=2,default=0.00)
    # 货款完结状态
    payment_completed = models.BooleanField(default=False, verbose_name="货款完结状态")
    # 发票完结状态
    invoice_completed = models.BooleanField(default=False, verbose_name="发票完结状态")
    # 合同附件
    attachment = models.FileField(upload_to=contract_attachment_path, verbose_name="合同附件", blank=True, null=True)
    # 合同备注，可记录改合同等信息，非必填
    remark = models.TextField(verbose_name="备注", blank=True, null=True)

    class Meta:
        # 定义数据库表名为'contract'
        db_table = 'contract'

    # 返回合同编号
    def __str__(self):
        return str(self.contract_number)
    # 计算合同已收金额
    def total_collection(self):
        return self.collection_set.all().aggregate(models.Sum('amount'))['amount__sum'] or 0
    # 合同已开发票金额
    def total_invoice(self):
        return self.invoice_set.all().aggregate(models.Sum('amount'))['amount__sum'] or 0

    # 合同回款百分比
    def collection_ratio(self):
        total_paid = self.total_collection()
        if self.total_price == 0:
            return 0
        return (total_paid / self.total_price) * 100
    # 合同发票百分比
    def invoice_ratio(self):
        total_invoiced = self.total_invoice()
        if self.total_price == 0:
            return 0
        return (total_invoiced / self.total_price) * 100
    # 合同未收金额
    def outstanding_balance(self):
        return self.total_price - self.total_collection()
    # 更新回款完结状态
    def update_payment_completed_status(self):
        # 计算已付款金额
        total_paid = Collection.objects.filter(contract=self).aggregate(models.Sum('amount'))['amount__sum'] or 0
        # 更新完结状态
        self.payment_completed = total_paid >= self.total_price
        self.save()
    # 更新发票完结状态
    def update_invoice_completed_status(self):
        # 计算已付款金额
        total_paid = Invoice.objects.filter(contract=self).aggregate(models.Sum('amount'))['amount__sum'] or 0
        # 更新完结状态
        self.invoice_completed = total_paid >= self.total_price
        self.save()

#合同产品表
class Contract_Product(models.Model):
    # 合同编号
    contract = models.ForeignKey(verbose_name="合同编号", to="Contract", on_delete=models.PROTECT)
    #客户名称
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT,default=1)
    # 产品名称
    category = models.ForeignKey(verbose_name="产品名称", to="ProductCategory", on_delete=models.PROTECT)
    # 产品型号
    product = models.ForeignKey(verbose_name="产品型号", to="Product", on_delete=models.PROTECT)
    #是维修还是销售
    contract_type = models.CharField(verbose_name="合同类型", max_length=16, choices=(("sale", "销售服务"), ("repair", "维修服务")),default="sale")
    # 产品数量 正数
    quantity = models.IntegerField(verbose_name="数量" ,validators=[MinValueValidator(1)])
    # 产品单价
    price = models.DecimalField(verbose_name="产品单价", max_digits=10, decimal_places=2)
    # 产品总价
    total_price = models.DecimalField(verbose_name="产品总价", max_digits=10, decimal_places=2)
    # 备注
    description = models.CharField(verbose_name="备注", max_length=128, blank=True, null=True)

    class Meta:
        # 定义数据库表名为'contract_product'
        db_table = 'contract_product'

    def __str__(self):
        # 返回合同编号
        return str(self.contract)

#合同回款表
class Collection(ModelBase):
    """ 回款表 """
    # 客户名称
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT)
    # 合同编号
    contract = models.ForeignKey(verbose_name="合同编号", to="Contract", on_delete=models.PROTECT)
    # 回款日期
    date = models.DateField(verbose_name="回款日期", )
    # 回款金额
    amount = models.DecimalField(verbose_name="回款金额", max_digits=10, decimal_places=2)
    # 回款方式
    collection_method_choices = (
        (1, "电汇"),
        (2, "银承"),
        (3, "现金"),
        (4, "万纳信"),
        (5, "迪链")
    )
    collection_method = models.IntegerField(verbose_name="回款方式", choices=collection_method_choices, default=1)

    class Meta:
        # 定义数据库表名为'collection'
        db_table = 'collection'

    # 更新合同状态
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.contract.update_payment_completed_status()

    def __str__(self):
        return f"Collection {self.id} for Contract {self.contract.contract_number}"

#合同发票
class Invoice(ModelBase):
    """ 发票登记表 """
    #日期
    date = models.DateField(verbose_name="日期")
    #客户名称
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT)
    #合同编号
    contract = models.ForeignKey(verbose_name="合同编号", to="Contract", on_delete=models.PROTECT)
    #发票号码
    invoice_number = models.CharField(verbose_name="发票号码", max_length=20)
    #开票金额
    amount = models.DecimalField(verbose_name="开票金额", max_digits=10, decimal_places=2)
    #开票人
    invoice_man = models.ForeignKey(verbose_name="开票人", to="User", on_delete=models.PROTECT)
    class Meta:
        # 定义数据库表名为'invoice'
        db_table = 'invoice'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.contract.update_invoice_completed_status()

    def __str__(self):
        return f"Invoice {self.id} for Contract {self.contract.contract_number}"

# 售后服务
class Service(ModelBase):
    """ 服务表 """
    # 客户名称
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT)
    # 产品名称
    productcategory = models.ForeignKey(verbose_name="产品名称", to="ProductCategory", on_delete=models.PROTECT)
    # 产品型号
    product = models.ForeignKey(verbose_name="产品型号", to="Product", on_delete=models.PROTECT)
    #维修编号
    service_number = models.CharField(verbose_name="维修编号", max_length=20)
    #产品编号
    product_number = models.CharField(verbose_name="产品编号", max_length=20, blank=True, null=True)
    WARRANTY_CHOICES = (
        (1, "质保外"),
        (2, "质保内"),
    )
    # 质保状态
    warranty = models.IntegerField(verbose_name="质保状态", choices=WARRANTY_CHOICES, default=1)
    #售后完结
    WARRANTY_END_CHOICES = (
        (1, "正在维修"),
        (2, "维修完成"),
    )
    # 售后完结状态
    warranty_end = models.IntegerField(verbose_name="售后完结", choices=WARRANTY_END_CHOICES, default=1)
    #返件状态
    RETURN_CHOICES = (
        (1, "未发货"),
        (2, "已发货"),
    )
    return_status = models.IntegerField(verbose_name="返件状态", choices=RETURN_CHOICES, default=1)
    #接收日期
    date = models.DateField(verbose_name="接收日期")
    #责任人
    repairman = models.ForeignKey(verbose_name="责任人", to="User", on_delete=models.PROTECT,default=17)
    #备注
    description = models.CharField(verbose_name="备注", max_length=128, blank=True, null=True)

    class Meta:
        # 定义数据库表名为'service'
        db_table = 'service'

    def __str__(self):
        return str(self.service_number)

#售后维修
class ServiceDetail(ModelBase):
    """ 服务明细表 """
    #客户名称
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT,default=1)
    #服务编号
    service = models.ForeignKey(verbose_name="维修编号", to="Service", on_delete=models.PROTECT)
    #产品名称
    productcategory = models.ForeignKey(verbose_name="产品名称", to="ProductCategory", on_delete=models.PROTECT,blank=True, null=True)
    #产品型号
    product = models.ForeignKey(verbose_name="产品型号", to="Product", on_delete=models.PROTECT,blank=True, null=True)
    #维修人
    repairman = models.ForeignKey(verbose_name="维修人", to="User", on_delete=models.PROTECT)
    #故障现象
    fault_text = models.TextField(verbose_name="故障现象")
    #故障原因
    fault_reason = models.TextField(verbose_name="故障原因")
    #维修方法
    repair_method = models.TextField(verbose_name="维修方法")
    #维修时间
    repair_date = models.DateField(verbose_name="维修完成时间")
    class Meta:
        db_table = 'service_detail'
    def __str__(self):
        return str(self.service)

#售后返件
class ReturnProduct(ModelBase):
    """ 售后返件登记表 """
    # 客户名称
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT)
    #服务编号
    service = models.ForeignKey(verbose_name="维修编号", to="Service", on_delete=models.PROTECT,)
    #自动日期
    date = models.DateField(verbose_name="日期")
    #发货人
    user = models.ForeignKey(verbose_name="发货人", to="User", on_delete=models.PROTECT,default=17)
    class Meta:
        db_table = 'return_product'

#生产计划表
class Plan(ModelBase):
    """ 生产计划表 """
    #合同编号
    contract = models.ForeignKey(verbose_name="合同编号", to="Contract", on_delete=models.PROTECT)
    #备用编号
    contract_reserve = models.CharField(verbose_name="备用编号", max_length=20,blank=True, null=True)
    #产品名称
    productcategory = models.ForeignKey(verbose_name="产品名称", to="ProductCategory", on_delete=models.PROTECT)
    #产品型号
    product = models.ForeignKey(verbose_name="产品型号", to="Product", on_delete=models.PROTECT)
    #数量
    quantity = models.IntegerField(verbose_name="数量",validators=[MinValueValidator(1)])
    #制单人
    production_man = models.ForeignKey(verbose_name="制单人", to="User", on_delete=models.PROTECT,default=1)
    #单位
    UNIT_CHOICES = (
        (1, "台"),
        (2, "套"),
        (3, "个"),
    )
    unit = models.IntegerField(verbose_name="单位", choices=UNIT_CHOICES, default=1)
    #详细配置信息
    configuration = models.TextField(verbose_name="详细配置信息")
    #合同生效日期
    effective_date = models.DateField(verbose_name="生效日期")
    #交货日期
    delivery_date = models.DateField(verbose_name="交货日期")
    #任务单状态
    STATUS_CHOICES = (
        (1, "待生产"),
        (2, "生产中"),
        (3, "已完成"),
    )
    completed_status = models.IntegerField(verbose_name="任务单状态", choices=STATUS_CHOICES, default=1)
    #完结状态
    completed = models.BooleanField(default=False, verbose_name="完结状态")

    class Meta:
        # 定义数据库表名为'plan'
        db_table = 'plan'

    @property
    def is_temp_plan(self):
        """无合同临时计划：挂在备用合同下的计划"""
        return self.contract.contract_number == TEMP_CONTRACT_NUMBER

    def __str__(self):
        # 返回合同编号
        return str(self.contract)

#生产任务单
class ProductionTask(ModelBase):
    # 合同编号
    contract = models.ForeignKey(verbose_name="合同编号", to="Plan", on_delete=models.PROTECT)
    #日期
    date = models.DateField(verbose_name="日期")
    # 产品名称
    productcategory = models.CharField(verbose_name="产品名称",max_length=32,blank=True, null=True)
    # 产品型号
    product = models.CharField(verbose_name="产品型号",max_length=32,blank=True, null=True)
    # 数量
    quantity = models.IntegerField(verbose_name="数量",blank=True, null=True)
    # 负责人
    production_man = models.ForeignKey(verbose_name="负责人", to="User", on_delete=models.PROTECT,default=1)
    class Meta:
        db_table = 'production_task'

# 合同文件路径
def contract_file_path(instance, filename):
    # 获取合同编号
    contract_number = instance.contract
    # 返回合同编号和文件名
    return f'{contract_number}/{filename}'

# 合同文件
class ContractFile(ModelBase):
    """ 合同文件表 """
    # 合同编号
    contract = models.ForeignKey(verbose_name="合同编号", to="Plan", on_delete=models.PROTECT )
    #电气原理图
    electrical_drawings = models.FileField(upload_to=contract_file_path,verbose_name='电气原理图', blank=True, null=True)
    #说明书
    instruction = models.FileField(upload_to=contract_file_path,verbose_name='说明书', blank=True, null=True)
    #装箱清单
    packing_list = models.FileField(upload_to=contract_file_path,verbose_name='装箱清单', blank=True, null=True)
    #机械图纸
    mechanical_drawings = models.FileField(upload_to=contract_file_path,verbose_name='机械图纸', blank=True, null=True)
    #其他文件
    other_file = models.FileField(upload_to=contract_file_path,verbose_name='其他文件', blank=True, null=True)

    class Meta:
        # 定义数据库表名为'contractfile'
        db_table = 'contractfile'

# 产品标牌
class ProductLabel(ModelBase):
    """ 产品标牌 """
    # 型号
    product = models.ForeignKey(verbose_name="型号", to="Product", on_delete=models.PROTECT)
    # 功率
    power = models.CharField(verbose_name="电源功率(kW)", max_length=20)
    # 频率
    frequency = models.CharField(verbose_name="电源频率(kHz)", max_length=20)
    # 供电容量
    sup_capacity = models.CharField(verbose_name="供电容量(kVA)", max_length=20)
    # 供电电压
    sup_voltage = models.CharField(verbose_name="供电电压(V)", max_length=20)
    # 供电频率
    sup_frequency = models.CharField(verbose_name="供电频率(Hz)", max_length=20)
    # 供电电流
    sup_current = models.CharField(verbose_name="供电电流(A)", max_length=20)
    # 最高进水温度
    max_in_temp = models.CharField(verbose_name="最高进水温度(°C)", max_length=20)
    # 最大压力
    max_pressure = models.CharField(verbose_name="最大压力(MPa)", max_length=20)
    # 最小流量
    min_flow = models.CharField(verbose_name="最小流量(L/min)", max_length=20)
    # 最小压力
    min_pressure = models.CharField(verbose_name="最小压力(MPa)", max_length=20)

    class Meta:
        db_table = 'productlabel'

# 产品发货
class ProductDelivery(ModelBase):
    """ 产品发货 """
    #客户名称
    customer = models.ForeignKey(verbose_name="客户名称", to="Customer", on_delete=models.PROTECT,default=1)
    #发货日期
    date = models.DateField(verbose_name="发货日期")
    #合同编号
    contract = models.ForeignKey(verbose_name="合同编号", to="Plan", on_delete=models.PROTECT)
    # 产品名称
    productcategory = models.CharField(verbose_name="产品名称", max_length=32, blank=True, null=True)
    # 产品型号
    product = models.CharField(verbose_name="产品型号", max_length=32, blank=True, null=True)
    # 数量
    quantity = models.IntegerField(verbose_name="数量", blank=True, null=True)
    #发货人
    delivery_man = models.ForeignKey(verbose_name="发货人", to="User", on_delete=models.PROTECT)

    class Meta:
        # 定义数据库表名为'product_delivery'
        db_table = 'product_delivery'


class Admin(models.Model):
    """ 管理员 """
    username = models.CharField(verbose_name="用户名", max_length=32)
    password = models.CharField(verbose_name="密码", max_length=64)

    def __str__(self):
        return self.username


class MyCompany(models.Model):
    """ 公司信息 """
    # 公司名称
    company_name = models.CharField(verbose_name="公司名称", max_length=32)
    #公司税号
    company_tax_number = models.CharField(verbose_name="公司税号", max_length=32)
    #银行账号
    company_bank_account = models.CharField(verbose_name="银行账号", max_length=32)
    #开户行
    company_bank = models.CharField(verbose_name="开户行", max_length=32)
    #银行行号
    company_bank_code = models.CharField(verbose_name="银行行号", max_length=32)
    # 公司地址
    company_address = models.CharField(verbose_name="公司地址", max_length=128)
    # 公司电话
    company_phone = models.CharField(verbose_name="公司电话", max_length=32)
    # 公司传真
    company_fax = models.CharField(verbose_name="公司传真", max_length=32)
    # 公司邮箱
    company_email = models.CharField(verbose_name="公司邮箱", max_length=32)
    # 公司网址
    company_website = models.CharField(verbose_name="公司网址", max_length=32)


class UserLog(models.Model):
    user = models.ForeignKey(verbose_name="用户", to="User", on_delete=models.PROTECT)
    action = models.CharField(max_length=255)
    ip = models.CharField(max_length=64,default="192.168.1.1")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.action}'


class AuthRole(models.Model):
    """ 网页端可管理的角色配置 """
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
    """ 单个用户相对角色的权限/栏目覆盖 """
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
    """ 平台账号密码备忘 """
    # 分类，如：网站平台、银行、邮箱、服务器
    category = models.CharField(verbose_name="分类", max_length=32, blank=True, null=True)
    # 平台名称
    name = models.CharField(verbose_name="平台名称", max_length=64)
    # 平台网址
    url = models.CharField(verbose_name="网址", max_length=255, blank=True, null=True)
    # 登录用户名
    account = models.CharField(verbose_name="登录账号", max_length=128, blank=True, null=True)
    # 登录密码
    password = models.CharField(verbose_name="登录密码", max_length=128, blank=True, null=True)
    # 其他备忘文本，如密保问题、绑定的手机邮箱等
    remark = models.TextField(verbose_name="备注", blank=True, null=True)

    class Meta:
        # 定义数据库表名为'account_vault'
        db_table = 'account_vault'
        ordering = ['-id']

    def __str__(self):
        return self.name
