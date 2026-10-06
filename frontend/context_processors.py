import os
from django.conf import settings

def company_context(request):
    """Context processor providing company branding and metadata to templates."""
    role = "admin"
    if request.user.is_authenticated:
        if hasattr(request.user, "profile"):
            role = request.user.profile.role
        elif request.user.is_superuser or request.user.is_staff:
            role = "admin"
        else:
            role = "employee"

    return {
        "COMPANY_NAME": os.environ.get("COMPANY_NAME", "OMS Operations"),
        "COMPANY_EMAIL": os.environ.get("COMPANY_EMAIL", "operations@oms.com"),
        "COMPANY_PHONE": os.environ.get("COMPANY_PHONE", "+971 4 000 0000"),
        "COMPANY_ADDRESS": os.environ.get("COMPANY_ADDRESS", "Dubai, United Arab Emirates"),
        "USER_ROLE": role,
    }
