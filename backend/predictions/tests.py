from unittest.mock import patch

from django.test import TestCase

from cases.models import Case

from .models import Prediction
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
