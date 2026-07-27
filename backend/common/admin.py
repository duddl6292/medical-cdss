import os

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db.models import Q

from .models import AuditEvent, UserProfile

User = get_user_model()

admin.site.site_header = "MEDICAL CDSS 운영관리"
admin.site.site_title = "Medical CDSS Admin"
admin.site.index_title = "의료정보 시스템 관리"
admin.site.empty_value_display = "—"
admin.site.site_url = os.getenv(
    "CDSS_FRONTEND_URL",
    "https://medical-cdss-frontend-356595725907.asia-southeast1.run.app",
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 1
    max_num = 1
    verbose_name_plural = "의료기관 프로필 및 권한"
    fields = ("role", "department")


admin.site.unregister(User)


@admin.register(User)
class MedicalUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "display_name",
        "email",
        "profile_role",
        "profile_department",
        "is_active",
        "is_staff",
        "last_login",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "cdss_profile__role",
        "cdss_profile__department",
    )
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "cdss_profile__department",
    )
    ordering = ("username",)
    list_per_page = 30
    actions = ("activate_accounts", "deactivate_accounts")

    @admin.display(description="성명", ordering="last_name")
    def display_name(self, obj):
        return obj.get_full_name() or "미등록"

    @admin.display(description="직무 권한", ordering="cdss_profile__role")
    def profile_role(self, obj):
        if obj.is_superuser:
            return "시스템 관리자"
        profile = getattr(obj, "cdss_profile", None)
        return profile.get_role_display() if profile else "의료진"

    @admin.display(description="소속 부서", ordering="cdss_profile__department")
    def profile_department(self, obj):
        profile = getattr(obj, "cdss_profile", None)
        return profile.department if profile and profile.department else "미지정"

    @admin.action(description="선택 계정 사용 승인")
    def activate_accounts(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count}개 계정을 활성화했습니다.")

    @admin.action(description="선택 계정 사용 중지")
    def deactivate_accounts(self, request, queryset):
        protected = Q(pk=request.user.pk) | Q(is_superuser=True)
        count = queryset.exclude(protected).update(is_active=False)
        self.message_user(request, f"{count}개 계정을 비활성화했습니다.")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "department", "account_active", "account_staff")
    list_filter = ("role", "department", "user__is_active", "user__is_staff")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "department",
    )
    autocomplete_fields = ("user",)
    list_select_related = ("user",)
    list_per_page = 30

    @admin.display(description="계정 활성", boolean=True, ordering="user__is_active")
    def account_active(self, obj):
        return obj.user.is_active

    @admin.display(description="관리 화면 접근", boolean=True, ordering="user__is_staff")
    def account_staff(self, obj):
        return obj.user.is_staff


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action_label", "target_type", "target_id")
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("actor__username", "actor__email", "target_id", "action")
    readonly_fields = ("actor", "action", "target_type", "target_id", "metadata", "created_at")
    date_hierarchy = "created_at"
    list_select_related = ("actor",)
    list_per_page = 50

    @admin.display(description="이벤트", ordering="action")
    def action_label(self, obj):
        labels = {
            "auth.login": "로그인",
            "auth.logout": "로그아웃",
            "case.upload": "CT 업로드",
            "prediction.review": "분석 검토",
        }
        return labels.get(obj.action, obj.action)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
