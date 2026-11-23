"""售后流转 <-> 售后服务的桥接逻辑。

「送修」在售后流转里只是把板子标成维修中，真正的维修工单在老版售后服务里。
两边都要读写这段关联，单独放一层，避免 flow.py 与 service.py 互相 import。
"""
import datetime

from api.core import models

FLOW_DESCRIPTION_PREFIX = '从售后流转过来'


def write_status_log(archive, from_status, to_status, operator, remark=''):
    models.FlowStatusLog.objects.create(
        archive=archive,
        from_status=from_status,
        to_status=to_status,
        operator=operator,
        date=datetime.date.today(),
        remark=remark,
    )


def build_service_number():
    """CN2025WX{流水}，沿用老版格式。

    按 id 递增探测第一个空号，不用 Max(service_number)：
    流水过 999 后字符串比较会退回旧号。
    """
    last = models.Service.objects.order_by('-id').first()
    seq = (last.id if last else 0) + 1
    while models.Service.objects.filter(
            service_number='CN2025WX{:03d}'.format(seq)).exists():
        seq += 1
    return 'CN2025WX{:03d}'.format(seq)


def create_service_for_return(flow_return, archive, operator, remark=None):
    """送修返回：按返回登记自动建一条售后服务单。

    电路板编号取「最终那块板」的序列号——换板时是新板，不换板是原板。
    """
    flow = flow_return.flow_out
    description = '{}：{}'.format(FLOW_DESCRIPTION_PREFIX, flow.flow_number)
    if remark:
        description = '{}，{}'.format(description, remark)
    service = models.Service.objects.create(
        customer_id=flow.customer_id,
        productcategory_id=archive.productcategory_id,
        product_id=archive.product_id,
        service_number=build_service_number(),
        product_number=archive.serial_number,
        warranty=1,
        warranty_end=1,
        return_status=1,
        date=flow_return.actual_return_date,
        repairman_id=(operator.pk if operator else archive.handler_id),
        # 备注写死「从售后流转过来」，老版售后服务列表里能一眼认出这类工单
        description=description[:128],
    )
    return service


def complete_archive_repair(service, operator):
    """售后返件登记后：这块板的维修结束，档案回到公司库存。

    与「产品档案」页的「维修完成」是同一件事，共用一套状态日志。
    """
    flow_return = models.FlowReturn.objects.filter(
        service=service, is_delete=False).first()
    if flow_return is None:
        return None
    archive = flow_return.new_archive or flow_return.flow_out.archive
    if archive.status != 3:
        return archive
    write_status_log(archive, 3, 1, operator,
                     '售后返件登记，维修完成（维修单 {}）'.format(service.service_number))
    archive.status = 1
    archive.location_type = 1
    archive.customer = None
    archive.save(update_fields=['status', 'location_type', 'customer'])
    return archive


def reopen_archive_repair(service, operator):
    """撤销售后返件登记：维修单又回到「维修中」，档案也跟着回去。"""
    flow_return = models.FlowReturn.objects.filter(
        service=service, is_delete=False).first()
    if flow_return is None:
        return None
    archive = flow_return.new_archive or flow_return.flow_out.archive
    if archive.status != 1:
        return archive
    write_status_log(archive, 1, 3, operator,
                     '撤销售后返件登记，回到维修中（维修单 {}）'.format(service.service_number))
    archive.status = 3
    archive.location_type = 1
    archive.customer = None
    archive.save(update_fields=['status', 'location_type', 'customer'])
    return archive
