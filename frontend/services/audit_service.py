import json
from django.core.serializers.json import DjangoJSONEncoder
from frontend.models import AuditLog


def log_action(user, action, model_instance, changes=None, request=None):
    """
    Log an audit trail entry for an action performed on a model instance.
    """
    ip_address = None
    if request:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

    changes_str = ""
    if isinstance(changes, dict):
        changes_str = json.dumps(changes, cls=DjangoJSONEncoder)
    elif changes:
        changes_str = str(changes)

    user_obj = user if user and user.is_authenticated else None
    model_name = model_instance.__class__.__name__
    object_id = str(getattr(model_instance, "pk", ""))
    object_repr = str(model_instance)[:200]

    return AuditLog.objects.create(
        user=user_obj,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        changes=changes_str,
        ip_address=ip_address,
    )
