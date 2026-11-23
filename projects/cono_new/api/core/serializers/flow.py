"""售后流转（实物台账）序列化器"""
from rest_framework import serializers
from api.core import models


class ProductArchiveSerializer(serializers.ModelSerializer):
    productcategory_name = serializers.CharField(source='productcategory.name', read_only=True)
    product_model = serializers.CharField(source='product.model', read_only=True)
    handler_name = serializers.CharField(source='handler.username', read_only=True)
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    superseded_by_serial = serializers.CharField(source='superseded_by.serial_number', read_only=True)

    class Meta:
        model = models.ProductArchive
        fields = '__all__'
        # 状态与换板标记只能由流转动作或专用接口改写，不允许前端直接 PATCH
        read_only_fields = ('is_superseded', 'superseded_by')

    def validate_serial_number(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('产品序列号不能为空')
        qs = models.ProductArchive.objects.filter(serial_number=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('该产品序列号已存在')
        return value

    def validate(self, attrs):
        status = attrs.get('status', getattr(self.instance, 'status', 1))
        location = attrs.get('location_type', getattr(self.instance, 'location_type', 1))
        customer = attrs.get('customer', getattr(self.instance, 'customer', None))
        if status == 2 and not customer:
            raise serializers.ValidationError({'customer': '状态为「客户试用中」时必须选择客户'})
        if location == 2 and not customer:
            raise serializers.ValidationError({'customer': '位置为「客户」时必须选择客户'})
        if location == 1:
            attrs['customer'] = None
        return attrs


class FlowOutSerializer(serializers.ModelSerializer):
    archive_serial = serializers.CharField(source='archive.serial_number', read_only=True)
    productcategory_name = serializers.CharField(source='archive.productcategory.name', read_only=True)
    product_model = serializers.CharField(source='archive.product.model', read_only=True)
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    returned = serializers.SerializerMethodField()

    class Meta:
        model = models.FlowOut
        fields = '__all__'
        read_only_fields = ('status',)

    def get_returned(self, obj):
        return models.FlowReturn.objects.filter(flow_out=obj, is_delete=False).exists()

    def validate_flow_number(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('流转编号不能为空')
        qs = models.FlowOut.objects.filter(flow_number=value, is_delete=False)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('该流转编号已存在')
        return value

    def validate_archive(self, value):
        if self.instance is not None and value.pk != self.instance.archive_id:
            raise serializers.ValidationError('已登记的寄出单不能更换产品档案')
        if value.is_superseded:
            raise serializers.ValidationError('该档案已被换板接替，不能再寄出')
        if not value.is_active:
            raise serializers.ValidationError('该档案已停用，不能再寄出')
        if self.instance is None and value.status != 1:
            raise serializers.ValidationError('只有「公司库存」的档案才能寄出')
        return value


class FlowReturnSerializer(serializers.ModelSerializer):
    flow_number = serializers.CharField(source='flow_out.flow_number', read_only=True)
    customer_name = serializers.CharField(source='flow_out.customer.company_name', read_only=True)
    archive_serial = serializers.CharField(source='flow_out.archive.serial_number', read_only=True)
    new_archive_serial = serializers.CharField(source='new_archive.serial_number', read_only=True)
    result_status_display = serializers.CharField(source='get_result_status_display', read_only=True)
    service_number = serializers.CharField(source='service.service_number', read_only=True)

    class Meta:
        model = models.FlowReturn
        fields = '__all__'
        # 快照、换板新档案、售后服务单均由后端写入，不接受前端直传，避免伪造历史
        read_only_fields = ('snapshot_serial', 'snapshot_model', 'new_archive', 'service')

    def validate_flow_out(self, value):
        if self.instance is not None and value.pk != self.instance.flow_out_id:
            raise serializers.ValidationError('返回登记不能更换流转编号')
        if models.FlowReturn.objects.filter(
                flow_out=value, is_delete=False).exclude(
                pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError('该流转编号已登记过返回')
        if value.status != 1:
            raise serializers.ValidationError('该流转单已返回，不能重复登记')
        return value


class SerialTransitionSerializer(serializers.ModelSerializer):
    old_serial_number = serializers.CharField(source='old_archive.serial_number', read_only=True)
    new_serial_number = serializers.CharField(source='new_archive.serial_number', read_only=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True)

    class Meta:
        model = models.SerialTransition
        fields = '__all__'


class FlowStatusLogSerializer(serializers.ModelSerializer):
    archive_serial = serializers.CharField(source='archive.serial_number', read_only=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True)

    class Meta:
        model = models.FlowStatusLog
        fields = '__all__'
