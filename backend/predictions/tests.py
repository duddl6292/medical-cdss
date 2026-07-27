from io import BytesIO
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from cases.models import Case

from .models import Prediction, PredictionResult
from .services import dispatch_prediction


def _completed_payload(prediction):
    return {
        "schema_version": "1.0",
        "job_id": str(prediction.job_id),
        "case_id": prediction.case.ct_id,
        "status": "completed",
        "model_version": "1.0.0",
        "model": {
            "model_id": "stroke-bhsd-nnunet-25d-final-model",
            "model_version": "1.0.0",
            "folds": [0],
            "checkpoint": "checkpoint_best.pth",
        },
        "artifacts": {
            "mask_uri": "gs://bucket/results/job/mask.nii.gz",
            "result_json_uri": "gs://bucket/results/job/result.json",
            "preview_uri": None,
            "probability_uri": None,
            "entropy_uri": None,
            "uncertainty_uri": None,
        },
        "result": {
            "lesion_volume_ml": 12.5,
            "lesion_slice_count": 2,
            "lesion_slice_start": 4,
            "lesion_slice_end": 5,
            "max_lesion_slice": 5,
        },
        "performance": {
            "inference_seconds": 1.25,
            "gpu_peak_memory_mb": 2048.0,
        },
        "message": "AI 분석 결과이며 최종 진단을 대체하지 않습니다.",
    }


class PredictionServiceTests(TestCase):
    def test_completed_gateway_payload_is_persisted(self):
        case = Case.objects.create(
            ct_file="ct_files/sample.nii.gz",
        )
        prediction = Prediction.objects.create(case=case)

        with patch(
            "predictions.services._request_gateway",
            return_value=_completed_payload(prediction),
        ):
            dispatch_prediction(prediction)

        prediction.refresh_from_db()
        self.assertEqual(prediction.status, Prediction.Status.COMPLETED)
        self.assertEqual(prediction.progress, 100)
        self.assertEqual(
            prediction.result.model_version,
            "1.0.0",
        )
        self.assertEqual(
            prediction.result.mask_path,
            "gs://bucket/results/job/mask.nii.gz",
        )


@override_settings(GS_BUCKET_NAME="private-medical-data")
class PredictionArtifactViewTests(TestCase):
    def setUp(self):
        self.case = Case.objects.create(
            ct_file="ct_files/sample.nii.gz",
        )
        self.prediction = Prediction.objects.create(
            case=self.case,
            status=Prediction.Status.COMPLETED,
            progress=100,
        )
        self.result = PredictionResult.objects.create(
            prediction=self.prediction,
            model_id="test-model",
            model_version="1.0.0",
            folds=[0],
            checkpoint="checkpoint.pth",
            mask_path=(
                "gs://private-medical-data/results/job/mask.nii.gz"
            ),
        )

    def test_result_returns_backend_proxy_urls(self):
        response = self.client.get(
            f"/api/v1/result/{self.case.ct_id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["mask_nifti_url"],
            (
                f"http://testserver/api/v1/result/{self.case.ct_id}"
                "/artifacts/mask/"
            ),
        )

    @patch("predictions.views.storage.Client")
    def test_artifact_is_streamed_from_private_bucket(self, client_class):
        blob = Mock()
        blob.content_type = "application/gzip"
        blob.open.return_value = BytesIO(b"nifti-data")
        client_class.return_value.bucket.return_value.blob.return_value = blob

        response = self.client.get(
            (
                f"/api/v1/result/{self.case.ct_id}"
                "/artifacts/mask/?download=1"
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            b"".join(response.streaming_content),
            b"nifti-data",
        )
        client_class.return_value.bucket.assert_called_once_with(
            "private-medical-data"
        )
        blob_method = client_class.return_value.bucket.return_value.blob
        blob_method.assert_called_once_with("results/job/mask.nii.gz")

    @patch("predictions.views.storage.Client")
    def test_artifact_from_another_bucket_is_rejected(self, client_class):
        self.result.mask_path = "gs://unexpected-bucket/results/mask.nii.gz"
        self.result.save(update_fields=["mask_path"])

        response = self.client.get(
            (
                f"/api/v1/result/{self.case.ct_id}"
                "/artifacts/mask/"
            )
        )

        self.assertEqual(response.status_code, 404)
        client_class.assert_not_called()
