from django.conf import settings
from django.db import models

from core.models import UUIDTimeStampedModel


class AuditLog(UUIDTimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=80)
    old_data = models.JSONField(default=dict)
    new_data = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model_name", "object_id"], name="audit_object_idx"),
            models.Index(fields=["user", "created_at"], name="audit_user_created_idx"),
        ]

    def __str__(self):
        return f"{self.action}: {self.model_name} {self.object_id}"
