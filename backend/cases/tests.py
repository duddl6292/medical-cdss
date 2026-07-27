from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


class CaseApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="clinician",
            password="test",
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_case_upload_creates_waiting_prediction(self):
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("case-create"),
                    {
                        "subject_id": "DEMO-001",
                        "ct_file": SimpleUploadedFile(
                            "sample.nii.gz",
                            b"not-a-real-nifti",
                            content_type="application/gzip",
                        )
                    },
                )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "waiting")
        self.assertEqual(response.json()["subject_id"], "DEMO-001")
        self.assertIsInstance(response.json()["case_id"], int)
        self.assertIsInstance(response.json()["job_id"], str)
