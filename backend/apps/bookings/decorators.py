from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

def role_required(allowed_roles):
    """Декоратор для защиты представлений по роли"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                return HttpResponseForbidden(
                    f"Доступ запрещён. Требуется одна из ролей: {', '.join(allowed_roles)}"
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator