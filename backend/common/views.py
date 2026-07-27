from django.contrib.auth import authenticate, login, logout
from django.db import connection
from django.db.models import Count, Q
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from predictions.models import Prediction

from .models import AuditEvent, UserProfile


def user_payload(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if user.is_superuser:
        role = UserProfile.Role.ADMIN
        role_label = "관리자"
    else:
        role = profile.role
        role_label = profile.get_role_display()

    return {
        "id": user.pk,
        "username": user.username,
        "name": user.get_full_name().strip() or user.username,
        "email": user.email,
        "role": role,
        "role_label": role_label,
        "department": profile.department,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
    }


def prediction_payload(prediction):
    case = prediction.case
    return {
        "case_id": case.ct_id,
        "job_id": str(prediction.job_id),
        "subject_id": case.subject_id,
        "status": prediction.status,
        "progress": prediction.progress,
        "elapsed_time": prediction.elapsed_time,
        "review_status": case.review_status,
        "created_at": case.created_at,
        "updated_at": prediction.updated_at,
        "error_message": prediction.error_message or None,
    }


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrf_token": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", ""))
        user = authenticate(request, username=username, password=password)

        if user is None or not user.is_active:
            return Response(
                {"detail": "아이디 또는 비밀번호가 올바르지 않습니다."},
                status=400,
            )
        if not (user.is_staff or user.is_superuser):
            return Response(
                {"detail": "승인된 의료진 계정만 사용할 수 있습니다."},
                status=403,
            )

        login(request, user)
        AuditEvent.objects.create(actor=user, action="auth.login")
        return Response(user_payload(user))


class LogoutView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        AuditEvent.objects.create(actor=user, action="auth.logout")
        logout(request)
        return Response(status=204)


class CurrentUserView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(user_payload(request.user))


class DashboardView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Prediction.objects.select_related("case")
        counts = queryset.aggregate(
            total=Count("pk"),
            completed=Count("pk", filter=Q(status=Prediction.Status.COMPLETED)),
            processing=Count("pk", filter=Q(status=Prediction.Status.PROCESSING)),
            waiting=Count("pk", filter=Q(status=Prediction.Status.WAITING)),
            failed=Count("pk", filter=Q(status=Prediction.Status.FAILED)),
        )
        recent = queryset.order_by("-case__created_at")[:8]
        return Response(
            {
                "summary": counts,
                "recent": [prediction_payload(item) for item in recent],
                "generated_at": recent[0].updated_at if recent else None,
            }
        )


class NotificationView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        predictions = (
            Prediction.objects.select_related("case")
            .exclude(status=Prediction.Status.WAITING)
            .order_by("-updated_at")[:10]
        )
        return Response(
            {
                "count": len(predictions),
                "results": [prediction_payload(item) for item in predictions],
            }
        )


class SystemHealthView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        database_status = "online"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            database_status = "unavailable"

        return Response(
            {
                "status": (
                    "healthy"
                    if database_status == "online"
                    else "degraded"
                ),
                "services": {
                    "django": "online",
                    "database": database_status,
                    "inference": "configured",
                },
            }
        )
