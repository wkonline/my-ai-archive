from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import random
import time
from pathlib import Path
from django.conf import settings
from api.core.views.captcha import create_captcha, verify_captcha, record_attempt, CAPTCHA_CHARS


class CreateCaptchaView(APIView):
    """生成验证码并返回 base64 图片"""
    permission_classes = [AllowAny]

    def get(self, request):
        ip = _client_ip(request)
        n = record_attempt(ip)
        if n == -1:
            return JsonResponse({'detail': '尝试次数过多，请稍后再试'}, status=429)

        key, code = create_captcha()
        img = _gen_image(code)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode()

        return JsonResponse({
            'key': key,
            'image': f'data:image/png;base64,{b64}',
        })


def _client_ip(request) -> str:
    """取真实客户端 IP。

    Nginx 与 API 都在 host 网络，REMOTE_ADDR 恒为 127.0.0.1；
    若按它做限流，等于全站共用一个配额，所有人一起被 429。
    """
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR', '')


def _gen_image(code: str) -> Image.Image:
    W, H = 120, 44
    img = Image.new('RGB', (W, H), color='#f0f4fa')
    draw = ImageDraw.Draw(img)
    # 干扰线
    for _ in range(3):
        x1, y1 = random.randint(0, W), random.randint(0, H)
        x2, y2 = random.randint(0, W), random.randint(0, H)
        draw.line([(x1, y1), (x2, y2)], fill='#c0d0e8', width=1)
    # 噪点
    for _ in range(40):
        px, py = random.randint(0, W-1), random.randint(0, H-1)
        draw.point((px, py), fill='#a0b8d0')
    # 文字：用项目根目录的 Monaco.ttf（随 Docker COPY . . 进入容器）
    font_path = Path(settings.BASE_DIR) / 'Monaco.ttf' if not str(settings.BASE_DIR).endswith('api') else Path(settings.BASE_DIR).parent / 'Monaco.ttf'
    try:
        font = ImageFont.truetype(str(font_path), 24)
    except Exception:
        font = ImageFont.load_default()
    color = '#0078e0'
    spacing = W // 4
    for i, ch in enumerate(code):
        x = spacing * i + random.randint(2, 6)
        y = random.randint(6, 14)
        draw.text((x, y), ch, fill=color, font=font)
    return img
