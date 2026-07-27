from django.contrib import admin

from .models import Case


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        "ct_id",
        "subject_id",
        "review_status",
        "uploaded_by",
        "created_at",
    )
    list_filter = ("review_status", "created_at")
    search_fields = ("subject_id",)
    readonly_fields = ("created_at",)
