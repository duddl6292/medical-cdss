from django.contrib import admin

from .models import Prediction, PredictionResult


class PredictionResultInline(admin.StackedInline):
    model = PredictionResult
    can_delete = False
    extra = 0
    max_num = 1
    readonly_fields = tuple(
        field.name
        for field in PredictionResult._meta.fields
        if field.name not in {"id", "prediction"}
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = (
        "job_id",
        "case",
        "subject_id",
        "status",
        "progress",
        "elapsed_time",
        "updated_at",
    )
    list_filter = ("status", "case__review_status", "updated_at")
    search_fields = ("job_id", "case__subject_id", "case__ct_id")
    readonly_fields = (
        "job_id",
        "case",
        "status",
        "progress",
        "elapsed_time",
        "error_code",
        "error_message",
        "updated_at",
    )
    date_hierarchy = "updated_at"
    list_select_related = ("case",)
    list_per_page = 50
    inlines = (PredictionResultInline,)

    @admin.display(description="비식별 대상 ID", ordering="case__subject_id")
    def subject_id(self, obj):
        return obj.case.subject_id

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PredictionResult)
class PredictionResultAdmin(admin.ModelAdmin):
    list_display = (
        "prediction",
        "model_id",
        "model_version",
        "lesion_volume_ml",
        "inference_time_seconds",
        "created_at",
    )
    search_fields = ("prediction__job_id", "prediction__case__subject_id", "model_id")
    readonly_fields = tuple(field.name for field in PredictionResult._meta.fields)
    list_select_related = ("prediction", "prediction__case")
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
