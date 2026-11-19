"""登录验证码：存放在 Django 缓存（文件缓存），多 worker 进程共享。

注意：不要用进程内 dict —— gunicorn 多 worker 时，验证码生成请求和登录请求
可能落到不同 worker，导致“验证码错误”随机出现。
"""
import random
import string
import time

from django.core.cache import cache

# 验证码字符集（去掉易混淆的 0/O/1/l/I）
CAPTCHA_CHARS = string.ascii_uppercase + string.digits
CAPTCHA_CHARS = ''.join(c for c in CAPTCHA_CHARS if c not in '0O1lI')

# 验证码有效期（秒）
EXPIRE_SECONDS = 300

# 每个 IP 最大尝试次数（60 秒窗口）
# 注意：每次打开登录页都会生成验证码，限流只用于挡住暴力刷新，不宜过严。
MAX_ATTEMPTS_PER_IP = 20


def _key(k: str) -> str:
    return f'captcha:{k}'


def _attempt_key(ip: str) -> str:
    return f'captcha_attempts:{ip or "unknown"}'


def gen_captcha_key() -> str:
    return ''.join(random.choices(CAPTCHA_CHARS, k=8))


def create_captcha() -> tuple[str, str]:
    """返回 (key, code) —— key 返回给前端，code 用于校验"""
    key = gen_captcha_key()
    code = ''.join(random.choices(CAPTCHA_CHARS, k=4))
    cache.set(_key(key), code, EXPIRE_SECONDS)
    return key, code


def verify_captcha(key: str, code: str) -> bool:
    if not key or not code:
        return False
    ck = _key(key)
    stored_code = cache.get(ck)
    if not stored_code:
        return False
    hit = stored_code.upper() == code.strip().upper()
    if hit:
        cache.delete(ck)  # 一次性验证
    return hit


def record_attempt(ip: str) -> int:
    """记录一次验证码生成请求；超过阈值返回 -1"""
    now = time.time()
    window = 60
    ck = _attempt_key(ip)
    attempts = [t for t in (cache.get(ck) or []) if now - t < window]
    attempts.append(now)
    cache.set(ck, attempts, window)
    if len(attempts) > MAX_ATTEMPTS_PER_IP:
        return -1
    return len(attempts)
