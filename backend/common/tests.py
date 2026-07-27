from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from cases.models import Case
from predictions.models import Prediction


class AuthenticationApiTests(TestCase):
    def setUp(self):
        self.password = "Strong-test-password-42!"
        self.user = get_user_model().objects.create_user(
            username="clinician",
            password=self.password,
            is_staff=True,
            first_name="Test",
            last_name="Clinician",
        )
        self.client = Client(enforce_csrf_checks=True)

    def test_session_login_me_and_logout(self):
        csrf_response = self.client.get(reverse("auth-csrf"))
        token = csrf_response.cookies["csrftoken"].value

        login_response = self.client.post(
            reverse("auth-login"),
            {"username": self.user.username, "password": self.password},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["role_label"], "의료진")

        me_response = self.client.get(reverse("auth-me"))
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["username"], "clinician")

        token = self.client.cookies["csrftoken"].value
        logout_response = self.client.post(
            reverse("auth-logout"),
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(logout_response.status_code, 204)
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 403)

    def test_login_rejects_missing_csrf_token(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": self.user.username, "password": self.password},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)


class DashboardApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="reviewer",
            password="test",
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_dashboard_uses_persisted_predictions(self):
        case = Case.objects.create(
            ct_file="ct_files/sample.nii.gz",
            subject_id="DEMO-001",
            uploaded_by=self.user,
        )
        Prediction.objects.create(
            case=case,
            status=Prediction.Status.COMPLETED,
            progress=100,
        )

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"]["total"], 1)
        self.assertEqual(
            response.json()["recent"][0]["subject_id"],
            "DEMO-001",
        )


class MedicalAdminTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="hospital-admin",
            password="test-password",
            email="admin@example.com",
        )
        self.client.force_login(self.admin)

    def test_admin_index_uses_medical_operations_branding(self):
        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MEDICAL CDSS")
        self.assertContains(response, "의료정보 시스템 관리")
        self.assertContains(response, "admin/css/medical_admin.css")
        self.assertContains(
            response,
            "https://medical-cdss-frontend-356595725907"
            ".asia-southeast1.run.app",
        )
        self.assertNotContains(response, 'target="_blank"')

    def test_user_changelist_supports_profileless_existing_accounts(self):
        response = self.client.get("/admin/auth/user/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hospital-admin")
        self.assertContains(response, "시스템 관리자")
