import copy
from django.template import Library
from django.conf import settings
from cono import models
from cono.tools.auth_profile import get_effective_menus

register = Library()


MENU_ICONS = {
    '合同管理': 'glyphicon-briefcase',
    '回款登记': 'glyphicon-piggy-bank',
    '发票登记': 'glyphicon-list-alt',
    '生产计划': 'glyphicon-cog',
    '资料上传': 'glyphicon-cloud-upload',
    '派任务单': 'glyphicon-send',
    '产品铭牌': 'glyphicon-barcode',
    '发货信息': 'glyphicon-shopping-cart',
    '仓库管理': 'glyphicon-compressed',
    '部门管理': 'glyphicon-th-large',
    '用户管理': 'glyphicon-user',
    '客户管理': 'glyphicon-user',
    '产品分类': 'glyphicon-tags',
    '产品管理': 'glyphicon-tag',
    '售后服务': 'glyphicon-earphone',
    '维修服务': 'glyphicon-wrench',
    '售后返件': 'glyphicon-transfer',
    '应收应付': 'glyphicon-stats',
    '数据备份': 'glyphicon-hdd',
    '操作日志': 'glyphicon-time',
    '公司信息': 'glyphicon-tower',
    '账号密码': 'glyphicon-lock',
    '权限管理': 'glyphicon-lock',
}


def menu_icon(title):
    return MENU_ICONS.get(title, 'glyphicon-th-large')


@register.inclusion_tag("menu.html")
def cono_menu(request):
    # 获取当前用户角色
    role = request.info_dict_role
    # 根据当前用户角色获取对应的菜单列表
    user = models.User.objects.filter(id=request.info_dict_useid).first()
    if user:
        user_menu_list = copy.deepcopy(get_effective_menus(user))
    else:
        user_menu_list = copy.deepcopy(settings.CONO_MENU.get(role, []))
    for row in user_menu_list:
        if request.path_info.startswith(row['url']):
            row['class'] = 'active'
        row['icon'] = menu_icon(row.get('title', ''))
    # 返回菜单列表到模板
    return {'user_menu_list': user_menu_list, 'request': request}


@register.filter
def home_status_class(value):
    """生产计划状态对应的首页颜色样式。"""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return ''
    if value == 2:
        return 'warning'
    if value == 3:
        return 'success'
    return 'danger'
