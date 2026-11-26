from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken as BaseRefreshToken
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from api.core.authentication import CoreUserJWTAuthentication
from api.core.models import User, Department
from api.core.views.captcha import verify_captcha
from api.core.permissions import get_effective_permissions, get_effective_menus


# 记住登录的可选周期（秒）：当天、一周、一个月
REMEMBER_TODAY = 86400
REMEMBER_WEEK = 604800
REMEMBER_MONTH = 2592000
ALLOWED_REMEMBER_DURATIONS = {REMEMBER_TODAY, REMEMBER_WEEK, REMEMBER_MONTH}
DEFAULT_REMEMBER_DURATION = REMEMBER_WEEK


def _remember_lifetime(remember_duration):
    """把前端的记忆周期转换成令牌有效期；当天截止到本地当天 23:59:59。"""
    if remember_duration == REMEMBER_TODAY:
        now = timezone.localtime()
        end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return end_of_today - now
    return timedelta(seconds=remember_duration)


class RefreshToken(BaseRefreshToken):
    """支持登录时指定有效期的 refresh token。"""

    @classmethod
    def for_user(cls, user, lifetime=None):
        token = super().for_user(user)
        if lifetime is not None:
            token.set_exp(lifetime=lifetime)
        return token

    @property
    def access_token(self):
        """让 access token 与记住登录的截止时间完全一致。"""
        token = super().access_token
        token.payload["exp"] = self.payload["exp"]
        return token


def _hash_password(password: str) -> str:
    """统一密码哈希：md5(老系统 SECRET_KEY + password)，见 cono.tools.password。"""
    from cono.tools.password import hash_password
    return hash_password(password)


class LoginView(APIView):
    """登录：校验老版 User 表账号，返回 JWT"""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        captcha_key = request.data.get('captcha_key', '')
        captcha_code = request.data.get('captcha_code', '')
        remember_duration = request.data.get(
            'rememberDuration',
            request.data.get('remember_duration', DEFAULT_REMEMBER_DURATION),
        )
        try:
            remember_duration = int(remember_duration)
        except (TypeError, ValueError):
            remember_duration = DEFAULT_REMEMBER_DURATION
        if remember_duration not in ALLOWED_REMEMBER_DURATIONS:
            remember_duration = DEFAULT_REMEMBER_DURATION

        if not verify_captcha(captcha_key, captcha_code):
            return Response({'detail': '验证码错误'}, status=400)

        # 空密码必须直接拒绝：Q(password='') 会匹配到密码为空的账号，
        # 老版 LoginForm.clean_password 同样禁止空密码。
        if not str(password).strip():
            return Response({'detail': '用户名或密码错误'}, status=401)

        from django.db.models import Q
        from cono.tools.password import candidate_salts, md5_hash
        # 库中哈希可能由不同盐值生成（历史账号），逐个候选盐比对
        candidates = [md5_hash(salt, password) for salt in candidate_salts()]
        user = User.objects.filter(username=username).filter(
            Q(password__in=candidates) | Q(password=password)
        ).first()
        if not user:
            return Response({'detail': '用户名或密码错误'}, status=401)
        refresh = RefreshToken.for_user(user, lifetime=_remember_lifetime(remember_duration))
        perms = get_effective_permissions(user)
        menus = get_effective_menus(user)
        expires_at = int(refresh.payload['exp'] * 1000)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'remember_duration': remember_duration,
            'expires_at': expires_at,
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.username,
                'role': user.role,
                'role_display': user.role_display,
                'permissions': sorted(perms) if perms is not None else [],
                'menus': menus,
            }
        })


class RegisterView(APIView):
    """用户注册：创建新账号并自动登录。

    默认关闭（settings.CONO_ALLOW_REGISTER），账号由管理员在用户管理里创建。
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from django.conf import settings
        if not getattr(settings, 'CONO_ALLOW_REGISTER', False):
            return Response({'detail': '系统未开放自助注册，请联系管理员创建账号'}, status=403)
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        confirm_password = request.data.get('confirm_password', '')
        captcha_key = request.data.get('captcha_key', '')
        captcha_code = request.data.get('captcha_code', '')

        phone = request.data.get('phone', '').strip()
        id_number = request.data.get('id_number', '').strip()
        address = request.data.get('address', '').strip()
        department_id = request.data.get('department_id', '')
        gender = request.data.get('gender', 1)  # 1=男, 2=女

        # 基础校验
        if not username or not password:
            return Response({'detail': '用户名和密码不能为空'}, status=400)
        if len(username) > 16:
            return Response({'detail': '用户名不能超过16个字符'}, status=400)
        if len(password) < 6:
            return Response({'detail': '密码至少6位'}, status=400)
        if password != confirm_password:
            return Response({'detail': '两次输入的密码不一致'}, status=400)

        # 员工表必填字段（数据库非空/唯一约束）
        if not phone:
            return Response({'detail': '请填写手机号'}, status=400)
        if not phone.isdigit() or len(phone) != 11:
            return Response({'detail': '手机号格式不正确'}, status=400)
        if not id_number:
            return Response({'detail': '请填写身份证号'}, status=400)
        if not (id_number.isdigit() and len(id_number) == 18):
            return Response({'detail': '身份证号应为18位数字'}, status=400)

        # 验证码校验
        if not verify_captcha(captcha_key, captcha_code):
            return Response({'detail': '验证码错误'}, status=400)

        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            return Response({'detail': '用户名已存在'}, status=400)

        # 身份证号唯一性校验
        if User.objects.filter(id_number=id_number).exists():
            return Response({'detail': '身份证号已被注册'}, status=400)

        # 部门校验
        if department_id:
            try:
                department = Department.objects.get(id=department_id)
            except (Department.DoesNotExist, ValueError):
                return Response({'detail': '部门不存在'}, status=400)
        else:
            department = Department.objects.first()
            if not department:
                return Response({'detail': '系统暂无可用部门，请联系管理员'}, status=400)

        try:
            gender = int(gender)
        except (TypeError, ValueError):
            gender = 1
        if gender not in (1, 2):
            gender = 1

        # 自助注册一律使用最低权限角色，忽略前端传入的 role，避免越权。
        from cono.tools.auth_profile import default_role_key
        try:
            with transaction.atomic():
                user = User.objects.create(
                    username=username,
                    password=_hash_password(password),
                    phone=phone,
                    id_number=id_number,
                    address=address or '',
                    department=department,
                    role=default_role_key(),
                    gender=gender,
                    create_date=timezone.now().date(),
                )
        except Exception as e:
            return Response({'detail': f'注册失败：{str(e)}'}, status=500)

        # 自动登录，返回 token
        remember_duration = request.data.get(
            'rememberDuration',
            request.data.get('remember_duration', DEFAULT_REMEMBER_DURATION),
        )
        try:
            remember_duration = int(remember_duration)
        except (TypeError, ValueError):
            remember_duration = DEFAULT_REMEMBER_DURATION
        if remember_duration not in ALLOWED_REMEMBER_DURATIONS:
            remember_duration = DEFAULT_REMEMBER_DURATION

        refresh = RefreshToken.for_user(user, lifetime=_remember_lifetime(remember_duration))
        perms = get_effective_permissions(user)
        menus = get_effective_menus(user)
        expires_at = int(refresh.payload['exp'] * 1000)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'remember_duration': remember_duration,
            'expires_at': expires_at,
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.username,
                'role': user.role,
                'role_display': user.role_display,
                'permissions': sorted(perms) if perms is not None else [],
                'menus': menus,
            }
        })


class ChangePasswordView(APIView):
    """修改密码：校验旧密码后更新，成功后需重新登录。"""
    authentication_classes = [CoreUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password', '').strip()
        new_password = request.data.get('new_password', '').strip()
        confirm_password = request.data.get('confirm_password', '').strip()

        if not old_password or not new_password:
            return Response({'detail': '请填写完整'}, status=400)
        if len(new_password) < 6:
            return Response({'detail': '新密码至少6位'}, status=400)
        if new_password != confirm_password:
            return Response({'detail': '两次输入的密码不一致'}, status=400)

        user = request.user
        if not user or not user.is_authenticated:
            return Response({'detail': '请先登录'}, status=401)

        from cono.tools.password import verify_password
        if not verify_password(user.password, old_password):
            return Response({'detail': '当前密码不正确'}, status=400)

        user.password = _hash_password(new_password)
        user.save()
        return Response({'message': '密码修改成功'})
