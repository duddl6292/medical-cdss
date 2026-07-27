from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        CLINICIAN = "clinician", "의료진"
        REVIEWER = "reviewer", "검토자"
        ADMIN = "admin", "관리자"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cdss_profile",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLINICIAN,
    )
    department = models.CharField(max_length=100, blank=True, default="")

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class AuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cdss_audit_events",
    )
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, blank=True, default="")
    target_id = models.CharField(max_length=128, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["actor", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} at {self.created_at.isoformat()}"
