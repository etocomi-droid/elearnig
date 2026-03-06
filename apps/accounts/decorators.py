from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from apps.accounts.models import ProjectMember


def project_permission_required(permission_name):
    """プロジェクト権限チェックデコレーター"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            project = getattr(request, 'current_project', None)
            if not project:
                return redirect('accounts:project_list')
            user = request.user
            # オーナーは常にOK
            if project.owner == user:
                return view_func(request, *args, **kwargs)
            # メンバーの権限チェック
            try:
                member = ProjectMember.objects.get(project=project, user=user)
                if member.role == 'admin' or getattr(member, permission_name, False):
                    return view_func(request, *args, **kwargs)
            except ProjectMember.DoesNotExist:
                pass
            messages.error(request, 'この操作の権限がありません。')
            return redirect('accounts:dashboard')
        return wrapper
    return decorator
