from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse


class CaseApiTests(TestCase):
    def test_case_upload_creates_waiting_prediction(self):
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("case-create"),
                    {
                        "ct_file": SimpleUploadedFile(
                            "sample.nii.gz",
                            b"not-a-real-nifti",
                            content_type="application/gzip",
                        )
                    },
                )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "waiting")
        self.assertIsInstance(response.json()["case_id"], int)
        self.assertIsInstance(response.json()["job_id"], str)
