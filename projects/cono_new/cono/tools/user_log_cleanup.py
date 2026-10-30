from datetime import timedelta

from django.utils import timezone

from cono import models


LOG_RETENTION_DAYS = 30
_last_cleanup_day = None


def cleanup_expired_user_logs():
    """删除超过 30 天的操作日志，返回本次删除数量。"""
    cutoff = timezone.now() - timedelta(days=LOG_RETENTION_DAYS)
    deleted, _ = models.UserLog.objects.filter(timestamp__lt=cutoff).delete()
    return deleted


def cleanup_expired_user_logs_daily():
    """每个进程每天最多执行一次日志清理。"""
    global _last_cleanup_day
    today = timezone.localdate()
    if _last_cleanup_day == today:
        return 0
    deleted = cleanup_expired_user_logs()
    _last_cleanup_day = today
    return deleted
