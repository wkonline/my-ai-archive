from cono import models
from django.core.exceptions import ValidationError
from cono.tools.bootstrap import BootStrapModelForm
from cono.tools.encrypt import md5
from django import forms
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

# 用户表单
class UserModelForm(BootStrapModelForm):

    class Meta:
        model = models.User
        # fields = "__all__"
        fields = ['username', "id_number", 'phone', 'address', "gender", "department"]


class ProfileEditModelForm(BootStrapModelForm):
    username = forms.CharField(
        label="用户名",
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
    )

    class Meta:
        model = models.User
        fields = ['username', 'id_number', 'phone', 'address', 'gender', 'department']


class RegisterUserModelForm(BootStrapModelForm):
    password = forms.CharField(
        label="登录密码",
        min_length=6,
        widget=forms.PasswordInput(render_value=True)
    )
    confirm_password = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(render_value=True)
    )
    code = forms.CharField(
        label="验证码",
        widget=forms.TextInput,
        required=True
    )

    class Meta:
        model = models.User
        fields = ['username', 'password', 'confirm_password', 'gender', 'id_number', 'phone', 'address', 'department']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and models.User.objects.filter(username=username).exists():
            raise ValidationError('该用户名已存在')
        return username

    def clean_password(self):
        pwd = self.cleaned_data.get('password')
        return md5(pwd)

    def clean_confirm_password(self):
        pwd = self.cleaned_data.get('password')
        confirm = md5(self.cleaned_data.get('confirm_password'))
        if confirm != pwd:
            raise ValidationError('两次输入的密码不一致')
        return confirm


# 收款表单
class CollectionModelForm(BootStrapModelForm):
    class Meta:
        model = models.Collection
        # exclude = ["customer", "contract"]
        fields = ['date', 'amount', 'collection_method']

# 客户表单
class CustomerModelForm(BootStrapModelForm):
    class Meta:
        model = models.Customer
        fields = ['company_name', 'contact_person', 'phone', 'address', 'saler']

# 仓库表单
class WarehouseModelForm(BootStrapModelForm):
    class Meta:
        model = models.Warehouse
        fields = "__all__"
        # labels = {
        #     'name':'仓库名称',
        # }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        queryset = models.Warehouse.objects.filter(name=name)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError('仓库名称已存在')
        return name

# 产品类别表单
class ProductCategoryModelForm(BootStrapModelForm):
    class Meta:
        model = models.ProductCategory
        fields = "__all__"
        # labels = {
        #     'name':'仓库名称',
        # }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        queryset = models.ProductCategory.objects.filter(name=name)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError('产品名称已存在')
        return name

# 产品表单
class ProductModelForm(BootStrapModelForm):
    class Meta:
        model = models.Product
        fields = "__all__"

# 合同表单
class ContractModelForm(BootStrapModelForm):
    bootstrap_exclude_fields = ['attachment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            from datetime import date
            today = date.today()
            default_number = 'CN{}W{:02d}{:02d}'.format(today.year, today.month, today.day)
            self.fields['contract_number'].initial = default_number
            self.fields['contract_number'].widget.attrs['value'] = default_number

    class Meta:
        model = models.Contract
        fields=["date","contract_number","attachment","remark"]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'remark': forms.Textarea(attrs={'rows': 3}),
        }

# 合同产品表单
class ContractProductModelForm(BootStrapModelForm):
    total_price = forms.DecimalField(required=False)

    class Meta:
        model = models.Contract_Product
        fields = ["category", "product", "price", "quantity", "total_price","contract_type"]

    def clean_total_price(self):
        quantity = self.cleaned_data.get("quantity")
        price = self.cleaned_data.get("price")
        if quantity is not None and price is not None:
            try:
                amount = (Decimal(quantity) * Decimal(price)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                return amount
            except (TypeError, ValueError, InvalidOperation):
                return Decimal("0.00")
        return self.cleaned_data.get("total_price") or Decimal("0.00")

# 产品集表单---添加用
Product_FormSet = forms.modelformset_factory(
    models.Contract_Product,
    form=ContractProductModelForm,
    extra=1,
    can_delete=False
)

# 产品集表单---更新用
Product_FormSet_update = forms.modelformset_factory(
    models.Contract_Product,
    form=ContractProductModelForm,
    extra=0,
    can_delete=True,
)


# 公告表单（老版公告管理页）
class AnnouncementForm(BootStrapModelForm):
    class Meta:
        model = models.Announcement
        fields = ['title', 'kind', 'is_top', 'is_active', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }


# 公司信息表单
class MyCompanyModelForm(BootStrapModelForm):
    class Meta:
        model = models.MyCompany
        fields = "__all__"


# 部门表单
class DepartmentModelForm(BootStrapModelForm):
    class Meta:
        model = models.Department
        fields = "__all__"

# 售后服务表单
class ServiceModelForm(BootStrapModelForm):
    class Meta:
        model = models.Service
        fields = ['customer', 'date', 'productcategory', 'product', 'product_number', 'warranty','description']

# 产品铭牌表单
class ProductLabelModelForm(BootStrapModelForm):
    class Meta:
        model = models.ProductLabel
        exclude = ['is_delete', 'product']

# 维修单表单
class ServiceDetailModelForm(BootStrapModelForm):
    class Meta:
        model = models.ServiceDetail
        fields= ['fault_text', 'fault_reason', 'repair_method', 'repair_date']

# 生产计划表单
class PlanModelForm(BootStrapModelForm):
    class Meta:
        model = models.Plan
        fields = ['contract_reserve', 'productcategory','product','quantity', 'unit', 'configuration', 'effective_date', 'delivery_date',]

# 合同文件表单
class ContractFileForm(BootStrapModelForm):
    bootstrap_exclude_fields = ['electrical_drawings', 'instruction', 'other_file', 'packing_list','mechanical_drawings']
    class Meta:
        model = models.ContractFile
        fields = ['electrical_drawings', 'instruction', 'other_file', 'packing_list','mechanical_drawings']

#电气图纸表单
class ElectricalFileForm(BootStrapModelForm):
    bootstrap_exclude_fields = ['electrical_drawings', 'instruction', 'other_file', 'packing_list','mechanical_drawings']
    class Meta:
        model = models.ContractFile
        fields = ['electrical_drawings', 'instruction',]

#机器图纸表单
class MechanicalFileForm(BootStrapModelForm):
    bootstrap_exclude_fields = ['electrical_drawings', 'instruction', 'other_file', 'packing_list','mechanical_drawings']
    class Meta:
        model = models.ContractFile
        fields = [ 'mechanical_drawings']

#项目文件表单
class BillFileForm(BootStrapModelForm):
    bootstrap_exclude_fields = ['electrical_drawings', 'instruction', 'other_file', 'packing_list','mechanical_drawings']
    class Meta:
        model = models.ContractFile
        fields = ['packing_list','other_file']

#发货表单
class DeliveryForm(BootStrapModelForm):

    class Meta:
        model = models.ProductDelivery
        fields = ['date']

#发票表单
class InvoiceModelForm(BootStrapModelForm):
    class Meta:
        model = models.Invoice
        fields = ['date','contract','amount', 'invoice_number']

#密码重置表单
class UserResetModelForm(BootStrapModelForm):

    confirm_password = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(render_value=True)
    )
    class Meta:
        model = models.User
        fields = ['password', 'confirm_password']
        widgets = {
            "password": forms.PasswordInput(render_value=True)
        }
    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        md5_pwd = md5(pwd)

        # 去数据库校验当前密码和新输入的密码是否一致
        exists = models.Admin.objects.filter(id=self.instance.pk, password=md5_pwd).exists()
        if exists:
            raise ValidationError("不能与以前的密码相同")

        return md5_pwd

    def clean_confirm_password(self):
        pwd = self.cleaned_data.get("password")
        confirm = md5(self.cleaned_data.get("confirm_password"))
        if confirm != pwd:
            raise ValidationError("密码不一致")
        # 返回什么，此字段以后保存到数据库就是什么。
        return confirm

class UploadFileForm(forms.Form):
    file = forms.FileField(label="请选择你需要上传的excel文件")


class ReturnProductModelForm(BootStrapModelForm):
    class Meta:
        model = models.ReturnProduct
        fields = ['date','service']


class TaskModelForm(BootStrapModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['date'].widget.format = '%Y-%m-%d'
        self.fields['date'].widget.input_type = 'date'

    class Meta:
        model = models.ProductionTask
        fields = ['date','productcategory','product', 'quantity']


# 平台账号密码表单
class AccountVaultModelForm(BootStrapModelForm):
    password = forms.CharField(
        label="登录密码",
        required=False,
        widget=forms.PasswordInput(render_value=True),
    )

    class Meta:
        model = models.AccountVault
        fields = ['category', 'name', 'url', 'account', 'password', 'remark']
        widgets = {
            'remark': forms.Textarea(attrs={'rows': 4}),
        }


# 修改密码表单
class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        label="旧密码",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password = forms.CharField(
        label="新密码",
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirm_password = forms.CharField(
        label="确认新密码",
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean_confirm_password(self):
        new_pwd = self.cleaned_data.get('new_password')
        confirm_pwd = self.cleaned_data.get('confirm_password')
        if new_pwd != confirm_pwd:
            raise forms.ValidationError('两次输入的密码不一致')
        return confirm_pwd
