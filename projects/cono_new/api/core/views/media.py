"""媒体文件视图：通过 Django 提供 media 文件。"""
import os
from django.conf import settings
from django.http import HttpResponse, Http404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def _resolve_path(path):
    """解析并验证路径，返回 (real_path, safe_root)。"""
    safe_root = os.path.realpath(settings.MEDIA_ROOT)
    requested = os.path.realpath(os.path.join(safe_root, path))
    if not requested.startswith(safe_root + os.sep) and requested != safe_root:
        raise Http404('Bad path')
    return requested, safe_root


def _get_mime(ext):
    mapping = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
        '.gif': 'image/gif', '.pdf': 'application/pdf',
        '.svg': 'image/svg+xml', '.webp': 'image/webp', '.mp4': 'video/mp4',
        '.mp3': 'audio/mpeg', '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.zip': 'application/zip',
    }
    return mapping.get(ext.lower(), 'application/octet-stream')


@api_view(['GET'])
@permission_classes([AllowAny])
def serve_media(request, path):
    """提供媒体文件。支持 ?format=json 返回 base64 data URL。"""
    try:
        requested, _ = _resolve_path(path)
    except Http404:
        return Response({'error': 'Bad path'}, status=404)

    if not os.path.isfile(requested):
        return Response({'error': 'File not found'}, status=404)

    ext = os.path.splitext(requested)[1]
    mime = _get_mime(ext)

    # JSON 模式：返回 base64 data URL（用于前端直接渲染）
    if request.GET.get('format') == 'json':
        import base64
        with open(requested, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        return Response({'data_url': f'data:{mime};base64,{b64}'})

    # 默认：返回原始文件流
    response = HttpResponse(content_type=mime)
    response['Content-Length'] = os.path.getsize(requested)
    with open(requested, 'rb') as f:
        response.write(f.read())
    return response
