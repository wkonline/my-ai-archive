"""系统模块：公司信息/操作日志/账号密码/权限管理"""
import re
from pathlib import Path
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import action
from core import models
from core.serializers.common import (
    CompanySerializer, UserLogSerializer,
    AuthRoleSerializer, AccountVaultSerializer,
)
from core.views.base import BaseModelViewSet


class CompanyViewSet(BaseModelViewSet):
    queryset = models.MyCompany.objects.all()
    serializer_class = CompanySerializer
    permission_codes = 'company_show'
    action_permission_codes = {
        'update': ['company_edit'],
        'partial_update': ['company_edit'],
    }


class UserLogViewSet(BaseModelViewSet):
    queryset = models.UserLog.objects.select_related('user').all()
    serializer_class = UserLogSerializer
    permission_codes = 'get_log'
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'action']
    ordering = ['-timestamp']

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by('-timestamp')

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """操作日志导出"""
        import datetime
        from io import BytesIO
        from django.http import HttpResponse
        import pandas as pd
        qs = self.get_queryset()
        data = [{
            '日期': str(log.timestamp),
            '用户': log.user.username if log.user else '',
            '操作内容': log.action,
            '记录IP': log.ip,
        } for log in qs]
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = 'log_data_{}.xlsx'.format(datetime.datetime.now().strftime('%Y%m%d'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response




def _permission_labels():
    """从老项目 cono/tools/auth_profile.py 读取权限中文描述。"""
    try:
        src = Path(__file__).resolve().parents[3] / 'cono' / 'tools' / 'auth_profile.py'
        text = src.read_text(encoding='utf-8')
        m = re.search(r'PERMISSION_LABELS = \{(.*?)\n\}', text, re.S)
        labels = {}
        if m:
            for line in m.group(1).splitlines():
                mm = re.match(r"\s*'([^']+)':\s*'([^']+)',", line)
                if mm:
                    labels[mm.group(1)] = mm.group(2)
        return labels
    except Exception:
        return {}


def _ensure_default_roles():
    """确保内置角色（admin/saler/servicer/upkeeper/finance）在 auth_role 表中存在。"""
    from django.conf import settings
    from core.models import AuthRole
    try:
        if AuthRole.objects.filter(key__in=['admin','saler','servicer','upkeeper','finance']).exists():
            return
    except Exception:
        return
    role_names = {
        'admin': '管理员', 'saler': '业务员', 'servicer': '客户经理',
        'upkeeper': '售后服务', 'finance': '财务经理',
    }
    cono_perm = getattr(settings, 'CONO_PERMISSION', {}) or {}
    cono_menu = getattr(settings, 'CONO_MENU', {}) or {}
    for key in ['admin','saler','servicer','upkeeper','finance']:
        if not AuthRole.objects.filter(key=key).exists():
            AuthRole.objects.create(
                key=key,
                name=role_names.get(key, key),
                permissions=sorted(set(cono_perm.get(key, []) or [])),
                menus=cono_menu.get(key, []) or [],
            )


class AuthRoleViewSet(BaseModelViewSet):
    queryset = models.AuthRole.objects.all()
    serializer_class = AuthRoleSerializer
    permission_codes = 'auth_role_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'key']

    def get_queryset(self):
        _ensure_default_roles()
        return super().get_queryset()

    @action(detail=False, methods=['get'], url_path='permission-options')
    def permission_options(self, request):
        """返回老版 CONO_PERMISSION / CONO_MENU / CONO_ROLE_NAMES 供前端勾选。"""
        _ensure_default_roles()
        from django.conf import settings
        from core.models import User

        role_names = {
            'admin': '管理员', 'saler': '业务员', 'servicer': '客户经理',
            'upkeeper': '售后服务', 'finance': '财务经理',
        }
        # Build grouped permissions (reuse old CONO_PERMISSION structure)
        cono_perm = getattr(settings, 'CONO_PERMISSION', {})
        cono_menu = getattr(settings, 'CONO_MENU', {})
        # Flatten all permission codes
        all_codes = set()
        for codes in cono_perm.values():
            all_codes.update(codes)
        return Response({
            'role_names': role_names,
            'permission_groups': cono_perm,
            'menu_groups': {k: v for k, v in cono_menu.items()},
            'all_codes': sorted(all_codes),
            'permission_labels': _permission_labels(),
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        return Response({'total': qs.count(), 'keys': list(qs.values_list('key', flat=True))})

    def destroy(self, request, *args, **kwargs):
        """删除角色时，将引用该角色的用户回退到 servicer（与老版一致）。"""
        role = self.get_object()
        if role.key in ('admin', 'saler', 'servicer', 'upkeeper', 'finance'):
            return Response(
                {'detail': f'内置角色 {role.key} 不可删除'}, status=400)
        models.User.objects.filter(role=role.key).update(role='servicer')
        role.delete()
        return Response(status=204)


class AccountVaultViewSet(BaseModelViewSet):
    queryset = models.AccountVault.objects.all()
    serializer_class = AccountVaultSerializer
    permission_codes = 'account_vault_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'account', 'category']
