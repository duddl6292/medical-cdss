from django.urls import path

from .views import (
    CsrfView,
    CurrentUserView,
    DashboardView,
    LoginView,
    LogoutView,
    NotificationView,
    SystemHealthView,
)

urlpatterns = [
    path("auth/csrf/", CsrfView.as_view(), name="auth-csrf"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", CurrentUserView.as_view(), name="auth-me"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("notifications/", NotificationView.as_view(), name="notifications"),
    path("system/health/", SystemHealthView.as_view(), name="system-health"),
]
