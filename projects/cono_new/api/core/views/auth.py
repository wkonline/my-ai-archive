from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from core.models import User


class LoginView(APIView):
    """登录：校验老版 User 表账号，返回 JWT"""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        # 老版密码存的是 md5(SECRET_KEY + password)，需一致哈希；
        # 同时兼容本地 SQLite 测试库的明文账号（如 admin/admin123）。
        from django.conf import settings
        from django.db.models import Q
        import hashlib

        def _md5(data):
            obj = hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
            obj.update(data.encode('utf-8'))
            return obj.hexdigest()

        hashed = _md5(password)
        user = User.objects.filter(username=username).filter(
            Q(password=hashed) | Q(password=password)
        ).first()
        if not user:
            return Response({'detail': '用户名或密码错误'}, status=401)
        refresh = RefreshToken.for_user(user)
        from core.permissions import get_effective_permissions, get_role_permissions, get_effective_menus
        perms = get_effective_permissions(user)
        menus = get_effective_menus(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.username,
                'role': user.role,
                'permissions': sorted(perms) if perms is not None else [],
                'menus': menus,
            }
        })
