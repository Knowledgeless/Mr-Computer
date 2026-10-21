from audit.models import AuditLog
from core.security import request_ip


def log_event(*, action, instance, user=None, request=None, old_data=None, new_data=None):
    return AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        model_name=instance._meta.label,
        object_id=str(instance.pk),
        old_data=old_data or {},
        new_data=new_data or {},
        ip_address=request_ip(request) if request else None,
    )
