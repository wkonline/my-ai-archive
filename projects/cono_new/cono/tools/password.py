"""密码哈希：与老系统兼容的 md5(盐 + 明文)。

历史原因，库里同一张 user 表的 password 可能由不同盐值生成：
早期账号用 settings.SECRET_KEY 的默认值，后来部署脚本又改成生产盐。
盐值一旦对不上，登录就一律提示"用户名或密码错误"，页面上看不出原因。

因此校验时按候选盐列表逐个尝试，写入时统一用主盐（settings.SECRET_KEY），
保证新密码只有一个格式，同时不让任何历史账号失去登录能力。
"""
import hashlib

from django.conf import settings

# 生产容器 cono_web 使用的盐，历史部署脚本注入过这个值
PRODUCTION_SALT = 'nas-cono-deploy-key-2026'


def md5_hash(salt, password):
    obj = hashlib.md5(salt.encode('utf-8'))
    obj.update(str(password).encode('utf-8'))
    return obj.hexdigest()


def candidate_salts():
    """校验时依次尝试的盐，顺序即优先级。

    当前 SECRET_KEY 排第一，其余是历史上真实用过的值。去重后返回，
    避免同一盐值被重复计算。
    """
    raw = [
        settings.SECRET_KEY,
        getattr(settings, 'LEGACY_SECRET_KEY', None),
        PRODUCTION_SALT,
        # 早期账号建立时 settings.py 里的默认值
        'django-insecure-$_+6ouqgn0hxgt19h&!1yh@^=@@x4xnzxg!zb=vyeg513kv$(j',
    ]
    seen, result = set(), []
    for salt in raw:
        if salt and salt not in seen:
            seen.add(salt)
            result.append(salt)
    return result


def verify_password(stored, password):
    """校验明文密码是否匹配库中哈希，命中任一候选盐即通过。

    stored 不是 32 位十六进制时（历史明文数据）直接按明文比对。
    """
    if not stored:
        return False
    if len(stored) != 32 or any(c not in '0123456789abcdef' for c in stored):
        return stored == str(password)
    return any(md5_hash(salt, password) == stored for salt in candidate_salts())


def shared_salt():
    """写入新密码用的盐：必须是新旧两套系统都认的那个。

    新 API 的 SECRET_KEY 是它自己独有的（生产里是 nas-cono-new-api-key-2026），
    老系统根本不知道这个值，用它写库会让账号在老系统永远登不上。
    因此写入统一走 LEGACY_SECRET_KEY（老系统的 SECRET_KEY），
    没设置时退回 SECRET_KEY（此时两边同值）。
    """
    return getattr(settings, 'LEGACY_SECRET_KEY', None) or settings.SECRET_KEY


def hash_password(password):
    """写入新密码时统一使用的哈希。"""
    return md5_hash(shared_salt(), password)
