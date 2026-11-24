"""系统模块：公司信息/操作日志/账号密码/权限管理"""
import re
from pathlib import Path
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import action
from api.core import models
from api.core.serializers.common import (
    CompanySerializer, UserLogSerializer,
    AuthRoleSerializer, AccountVaultSerializer,
)
from api.core.views.base import BaseModelViewSet


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
    # 只有“我的日志”对普通用户开放，不能看别人的日志
    action_permission_codes = {'mine': []}

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by('-timestamp')

    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request):
        """当前登录用户自己的最近操作（个人中心“我的资料”页用）"""
        qs = self.get_queryset().filter(user=request.user)[:10]
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """操作日志导出"""
        import datetime
        from io import BytesIO
        from django.http import HttpResponse
        import pandas as pd
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
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
    """补齐内置角色（admin/upkeeper），逻辑统一由 cono.tools.auth_profile 维护。

    业务员/客户经理/财务经理等已改为普通角色，被删除后不再自动重建。
    """
    from cono.tools.auth_profile import ensure_default_roles
    ensure_default_roles()


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
        """返回老版 CONO_PERMISSION / CONO_MENU / 内置角色名，供前端勾选。"""
        _ensure_default_roles()
        from django.conf import settings
        from cono.tools.auth_profile import ROLE_NAMES

        # Build grouped permissions (reuse old CONO_PERMISSION structure)
        cono_perm = getattr(settings, 'CONO_PERMISSION', {})
        cono_menu = getattr(settings, 'CONO_MENU', {})
        # Flatten all permission codes
        all_codes = set()
        for codes in cono_perm.values():
            all_codes.update(codes)
        return Response({
            'role_names': ROLE_NAMES,
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
        """删除角色：内置角色（admin/upkeeper）不可删，仍有用户使用的角色也不可删。

        不自动把用户改到别的角色：角色切换会静默改变用户权限，必须由管理员显式操作。
        """
        role = self.get_object()
        from cono.tools.auth_profile import is_builtin_role
        if is_builtin_role(role.key):
            return Response({'detail': f'内置角色 {role.key} 不可删除'}, status=400)
        in_use = models.User.objects.filter(role=role.key).count()
        if in_use:
            return Response(
                {'detail': f'还有 {in_use} 个用户属于该角色，请先在用户管理里改角色'}, status=400)
        role.delete()
        return Response(status=204)


class AccountVaultViewSet(BaseModelViewSet):
    queryset = models.AccountVault.objects.all()
    serializer_class = AccountVaultSerializer
    permission_codes = 'account_vault_list'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'account', 'category']
