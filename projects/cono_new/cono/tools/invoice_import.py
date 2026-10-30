"""金蝶销售发票序时簿与系统发票模板的解析、校验。

金蝶「销售发票(专用)序时簿」导出文件为多行结构：一张发票占用多行
（产品明细行），日期/发票号码/购货单位/订单单号等表头字段只写在
首行，其余行为空，需要在读取时向下填充还原归属关系。
"""
from decimal import Decimal, InvalidOperation

import pandas as pd

from cono import models


DEFAULT_INVOICE_MAN = '康毅飞'

ERROR_SUFFIX = '，请修改后再次上传'

KEY_COLUMNS = ['日期', '发票号码', '购货单位', '订单单号']

KINGDEE_AMOUNT_COLUMN = '价税合计'

SIMPLE_AMOUNT_COLUMN = '开票金额'


class InvoiceImportError(Exception):
    """发票导入校验失败，消息可直接展示给用户。"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _clean(value):
    if value is None:
        return ''
    try:
        if pd.isna(value):
            return ''
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return '' if text.lower() in ('nan', 'nat', 'none') else text


def _is_kingdee_frame(frame):
    return KINGDEE_AMOUNT_COLUMN in frame.columns and '产品名称' in frame.columns


def _parse_kingdee(frame):
    work = frame.copy()
    work['_row_no'] = work.index + 2

    mask = work['产品名称'].notna()
    if '审核标志' in work.columns:
        mask &= ~work['审核标志'].astype(str).str.contains('合计', na=False)
    work = work[mask].copy()
    if work.empty:
        raise InvoiceImportError('未在文件中找到发票数据' + ERROR_SUFFIX)

    work[KEY_COLUMNS] = work[KEY_COLUMNS].ffill()

    missing = work[work['发票号码'].isna()]
    if not missing.empty:
        raise InvoiceImportError('第 {} 行：缺少发票号码{}'.format(
            int(missing['_row_no'].iloc[0]), ERROR_SUFFIX))

    records = []
    for invoice_no, group in work.groupby('发票号码', sort=False):
        row_no = int(group['_row_no'].iloc[0])
        number = _clean(invoice_no)
        contract_numbers = {_clean(value) for value in group['订单单号']}
        contract_numbers.discard('')
        if len(contract_numbers) > 1:
            raise InvoiceImportError('第 {} 行：发票号码 {} 对应多个订单单号{}'.format(
                row_no, number, ERROR_SUFFIX))
        records.append({
            'row_no': row_no,
            'invoice_number': number,
            'contract_number': contract_numbers.pop() if contract_numbers else '',
            'customer_name': _clean(group['购货单位'].iloc[0]),
            'date': group['日期'].iloc[0],
            'amount': group[KINGDEE_AMOUNT_COLUMN].sum(),
        })
    return records


def _parse_simple(frame):
    records = []
    for index, row in frame.iterrows():
        records.append({
            'row_no': int(index) + 2,
            'invoice_number': _clean(row.get('发票号码')),
            'contract_number': _clean(row.get('订单单号')),
            'customer_name': _clean(row.get('购货单位')),
            'date': row.get('日期'),
            'amount': row.get(SIMPLE_AMOUNT_COLUMN),
        })
    return records


def read_invoice_file(uploaded_file):
    """读取上传的 Excel，返回标准化的发票记录列表。"""
    try:
        frame = pd.read_excel(uploaded_file, sheet_name=0)
    except ImportError as exc:
        # 服务器缺少读取 .xls 的依赖，属于部署问题，不能误导用户去改文件
        raise InvoiceImportError(
            '服务器缺少读取 .xls 的组件 xlrd，请管理员重建镜像后再上传。'
            '技术细节：{}'.format(exc)
        )
    except Exception as exc:
        # 带上真实原因，便于区分是文件问题还是部署问题
        raise InvoiceImportError(
            '无法读取该 Excel 文件，请确认是金蝶导出的发票序时簿。'
            '技术细节：{}: {}'.format(type(exc).__name__, exc)
        )

    if _is_kingdee_frame(frame):
        return _parse_kingdee(frame)
    if SIMPLE_AMOUNT_COLUMN in frame.columns:
        return _parse_simple(frame)
    raise InvoiceImportError('文件格式不正确，缺少发票号码、购货单位、订单单号、金额等列' + ERROR_SUFFIX)


def _parse_amount(value, row_no):
    try:
        amount = Decimal(str(round(float(value), 2)))
    except (InvalidOperation, TypeError, ValueError):
        raise InvoiceImportError('第 {} 行：发票金额格式不正确{}'.format(row_no, ERROR_SUFFIX))
    return amount.quantize(Decimal('0.01'))


def validate_records(records):
    """校验记录并返回可入库的数据，失败时抛出 InvoiceImportError。"""
    from cono.tools.form import InvoiceModelForm

    contracts = {contract.contract_number: contract for contract in models.Contract.objects.all()}
    customers = {customer.company_name.strip(): customer for customer in models.Customer.objects.all()}

    seen_numbers = set()
    prepared = []
    for record in records:
        row_no = record['row_no']
        number = record['invoice_number']
        if not number:
            raise InvoiceImportError('第 {} 行：发票号码为空{}'.format(row_no, ERROR_SUFFIX))
        if number in seen_numbers:
            raise InvoiceImportError('第 {} 行：发票号码 {} 在文件中重复{}'.format(row_no, number, ERROR_SUFFIX))
        if models.Invoice.objects.filter(invoice_number=number).exists():
            raise InvoiceImportError('第 {} 行：发票号码 {} 已登记{}'.format(row_no, number, ERROR_SUFFIX))
        seen_numbers.add(number)

        contract_number = record['contract_number']
        if not contract_number:
            raise InvoiceImportError('第 {} 行：订单单号为空{}'.format(row_no, ERROR_SUFFIX))
        contract = contracts.get(contract_number)
        if contract is None:
            raise InvoiceImportError('第 {} 行：订单单号 {} 在系统中不存在{}'.format(
                row_no, contract_number, ERROR_SUFFIX))

        customer_name = record['customer_name']
        if not customer_name:
            raise InvoiceImportError('第 {} 行：购货单位为空{}'.format(row_no, ERROR_SUFFIX))
        customer = customers.get(customer_name)
        if customer is None:
            raise InvoiceImportError('第 {} 行：购货单位 {} 在系统中不存在{}'.format(
                row_no, customer_name, ERROR_SUFFIX))
        if contract.customer_id != customer.id:
            raise InvoiceImportError('第 {} 行：购货单位“{}”与订单单号“{}”对应的客户不一致{}'.format(
                row_no, customer_name, contract_number, ERROR_SUFFIX))

        amount = _parse_amount(record['amount'], row_no)
        invoice_form = InvoiceModelForm({
            'contract': contract.id,
            'date': record['date'],
            'amount': amount,
            'invoice_number': number,
        })
        if not invoice_form.is_valid():
            field_name, field_errors = next(iter(invoice_form.errors.items()))
            raise InvoiceImportError('第 {} 行：{}格式不正确（{}）{}'.format(
                row_no, field_name, field_errors[0], ERROR_SUFFIX))

        prepared.append({
            'customer_id': customer.id,
            'contract_id': contract.id,
            'data': invoice_form.cleaned_data,
        })
    return prepared


def get_default_invoice_man_id(fallback_id):
    """开票人默认为康毅飞，找不到时退回当前登录用户。"""
    user = models.User.objects.filter(username=DEFAULT_INVOICE_MAN).first()
    return user.id if user else fallback_id
