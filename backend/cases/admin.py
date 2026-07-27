from django.contrib import admin

from .models import Case


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        "ct_id",
        "subject_id",
        "review_status",
        "uploaded_by",
        "reviewed_by",
        "created_at",
    )
    list_filter = ("review_status", "created_at", "uploaded_by")
    search_fields = (
        "subject_id",
        "uploaded_by__username",
        "reviewed_by__username",
    )
    readonly_fields = ("ct_id", "created_at")
    autocomplete_fields = ("uploaded_by", "reviewed_by")
    date_hierarchy = "created_at"
    list_select_related = ("uploaded_by", "reviewed_by")
    list_per_page = 50
    fieldsets = (
        (
            "검사 식별 정보",
            {"fields": ("ct_id", "subject_id", "ct_file", "created_at")},
        ),
        (
            "업로드 정보",
            {"fields": ("uploaded_by",)},
        ),
        (
            "의료진 검토",
            {
                "fields": (
                    "review_status",
                    "reviewed_by",
                    "reviewed_at",
                    "review_note",
                )
            },
        ),
    )
