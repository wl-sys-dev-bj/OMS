from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from rest_framework.permissions import BasePermission
from frontend.models import UserProfile


def get_user_role(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return UserProfile.Role.ADMIN
    if hasattr(user, "profile"):
        return user.profile.role
    return UserProfile.Role.EMPLOYEE


def role_required(allowed_roles):
    """
    Decorator for views that checks whether the user has one of the allowed roles.
    Superusers always pass.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            role = get_user_role(request.user)
            if role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to access this resource.")

        return _wrapped_view

    return decorator


def hr_or_admin_required(view_func):
    return role_required([UserProfile.Role.ADMIN, UserProfile.Role.HR])(view_func)


def finance_or_admin_required(view_func):
    return role_required([UserProfile.Role.ADMIN, UserProfile.Role.FINANCE])(view_func)


def manager_or_above_required(view_func):
    return role_required([UserProfile.Role.ADMIN, UserProfile.Role.HR, UserProfile.Role.MANAGER])(view_func)


# REST Framework Permission Classes
class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_superuser or get_user_role(request.user) == UserProfile.Role.ADMIN


class CanManageEmployees(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        role = get_user_role(request.user)
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return role in [UserProfile.Role.ADMIN, UserProfile.Role.HR, UserProfile.Role.MANAGER]


class CanManageExpenses(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        role = get_user_role(request.user)
        # Any authenticated user can create/view their expenses
        if request.method in ["GET", "HEAD", "OPTIONS", "POST"]:
            return True
        # Modification/deletion requires finance/admin/manager
        return role in [UserProfile.Role.ADMIN, UserProfile.Role.FINANCE, UserProfile.Role.MANAGER]


class CanApproveExpenses(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        role = get_user_role(request.user)
        return role in [UserProfile.Role.ADMIN, UserProfile.Role.FINANCE, UserProfile.Role.MANAGER]
