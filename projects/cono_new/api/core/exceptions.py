"""统一异常处理：把数据库约束类异常转成 400，避免前端看到 500。"""

import logging

from django.db import DataError, IntegrityError
from django.db.models import ProtectedError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

# 唯一约束 -> 中文提示。命中不到时用通用提示，绝不把 SQL 原文返回给前端。
UNIQUE_MESSAGES = (
    ('user.username', '用户名已存在'),
    ('user.id_number', '身份证号已被使用'),
    ('user.phone', '手机号已被使用'),
    ('customer.company_name', '客户名称已存在'),
    ('contract.contract_number', '合同编号已存在'),
    ('invoice.invoice_number', '发票号码已存在'),
    ('product.model', '产品型号已存在'),
    ('productcategory.name', '产品分类已存在'),
    ('warehouse.name', '仓库名称已存在'),
    ('department.title', '部门名称已存在'),
    ('service.service_number', '服务单号已存在'),
)


def _unique_message(text):
    for token, message in UNIQUE_MESSAGES:
        if token in text:
            return message
    return '数据重复，请检查后重试。'


def cono_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    view = context.get('view')
    view_name = type(view).__name__ if view else '?'
    request = context.get('request')

    if isinstance(exc, IntegrityError):
        text = str(exc).lower()
        if 'foreign key' in text or 'cannot delete' in text:
            detail = '该记录被其他数据引用，无法删除或修改。'
        elif 'duplicate' in text or 'unique' in text:
            detail = _unique_message(text)
        elif 'cannot be null' in text or 'not null' in text:
            detail = '必填字段不能为空。'
        else:
            detail = '数据保存失败，请检查填写内容。'
        logger.warning('%s IntegrityError: %s', view_name, exc)
        return Response({'detail': detail}, status=400)

    if isinstance(exc, ProtectedError):
        logger.warning('%s ProtectedError: %s', view_name, exc)
        return Response({'detail': '该记录被其他数据引用，无法删除。'}, status=400)

    if isinstance(exc, DataError):
        logger.warning('%s DataError: %s', view_name, exc)
        return Response({'detail': '数据超出允许范围（如金额过大或文字过长）。'}, status=400)

    # 其余异常交给 Django 记录堆栈并返回 500
    logger.exception('%s 未处理异常 (%s %s)',
                     view_name,
                     getattr(request, 'method', ''),
                     getattr(request, 'path', ''))
    return None
