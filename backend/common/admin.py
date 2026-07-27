from django.contrib import admin

from .models import AuditEvent, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "department")
    list_filter = ("role", "department")
    search_fields = ("user__username", "user__email", "department")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "actor",
        "action",
        "target_type",
        "target_id",
    )
    list_filter = ("action", "target_type")
    search_fields = ("actor__username", "target_id")
    readonly_fields = (
        "actor",
        "action",
        "target_type",
        "target_id",
        "metadata",
        "created_at",
    )
