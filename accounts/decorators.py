"""
Authentication and authorization decorators.
"""
from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from core.constants import UserRoles


def role_required(*roles):
    """
    Decorator to require specific user roles.
    
    Usage:
        @role_required(UserRoles.ADMIN, UserRoles.FACULTY)
        def my_view(request):
            pass
    
    Args:
        *roles: Variable number of role strings
        
    Returns:
        Decorated view function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            
            if request.user.role not in roles:
                messages.error(
                    request,
                    f"Access denied. Required role: {', '.join(roles)}"
                )
                raise PermissionDenied(
                    f"User role '{request.user.role}' not authorized. "
                    f"Required: {', '.join(roles)}"
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Convenience decorators for common role combinations
def admin_required(view_func):
    """Require ADMIN role"""
    return role_required(UserRoles.ADMIN)(view_func)


def faculty_required(view_func):
    """Require FACULTY role"""
    return role_required(UserRoles.FACULTY)(view_func)


def student_required(view_func):
    """Require STUDENT role"""
    return role_required(UserRoles.STUDENT)(view_func)


def admin_or_faculty_required(view_func):
    """Require ADMIN or FACULTY role"""
    return role_required(UserRoles.ADMIN, UserRoles.FACULTY)(view_func)


def admin_or_supervisor_required(view_func):
    """Require ADMIN or SUPERVISOR role"""
    return role_required(UserRoles.ADMIN, UserRoles.SUPERVISOR)(view_func)
