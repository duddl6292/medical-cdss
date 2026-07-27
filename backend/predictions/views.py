import mimetypes
from pathlib import PurePosixPath
from urllib.parse import urlparse

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from google.api_core.exceptions import NotFound
from google.cloud import storage
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Prediction
from .services import PredictionDispatchError, dispatch_prediction


RESULT_ARTIFACT_FIELDS = {
    "mask": "mask_path",
    "result": "result_json_uri",
    "preview": "preview_uri",
    "probability": "probability_uri",
    "entropy": "entropy_uri",
    "uncertainty": "uncertainty_uri",
}


def _artifact_url(request, prediction, artifact):
    return request.build_absolute_uri(
        reverse(
            "prediction-artifact",
            kwargs={
                "ct_id": prediction.case.ct_id,
                "artifact": artifact,
            },
        )
    )


def _optional_artifact_url(request, prediction, artifact, value):
    return _artifact_url(request, prediction, artifact) if value else None


def _parse_gcs_uri(uri):
    parsed = urlparse(uri)
    if (
        parsed.scheme != "gs"
        or parsed.netloc != settings.GS_BUCKET_NAME
        or not parsed.path.lstrip("/")
    ):
        raise Http404("Artifact is outside the configured private bucket.")
    return parsed.path.lstrip("/")


def _artifact_object_name(prediction, artifact):
    if artifact == "original":
        return prediction.case.ct_file.name

    field_name = RESULT_ARTIFACT_FIELDS.get(artifact)
    if field_name is None or not hasattr(prediction, "result"):
        raise Http404("Artifact not found.")

    uri = getattr(prediction.result, field_name)
    if not uri:
        raise Http404("Artifact not found.")
    return _parse_gcs_uri(uri)


def _prediction_status_payload(prediction):
    return {
        "case_id": prediction.case.ct_id,
        "job_id": str(prediction.job_id),
        "status": prediction.status,
        "progress": prediction.progress,
        "elapsed_time": prediction.elapsed_time,
        "error_code": prediction.error_code or None,
        "error_message": prediction.error_message or None,
        "created_at": prediction.case.created_at,
        "updated_at": prediction.updated_at,
    }


class PredictionStartView(APIView):
    def post(self, request, ct_id):
        prediction = get_object_or_404(
            Prediction.objects.select_related("case"),
            case__ct_id=ct_id,
        )

        if prediction.status == Prediction.Status.COMPLETED:
            return Response(_prediction_status_payload(prediction))

        if prediction.status == Prediction.Status.PROCESSING:
            return Response(
                _prediction_status_payload(prediction),
                status=status.HTTP_202_ACCEPTED,
            )

        try:
            dispatch_prediction(prediction)
        except PredictionDispatchError:
            prediction.refresh_from_db()
            return Response(
                _prediction_status_payload(prediction),
                status=status.HTTP_502_BAD_GATEWAY,
            )

        prediction.refresh_from_db()
        return Response(_prediction_status_payload(prediction))


class PredictionStatusView(APIView):
    def get(self, request, ct_id):
        prediction = get_object_or_404(
            Prediction,
            case__ct_id=ct_id,
        )

        return Response(_prediction_status_payload(prediction))
        
        
class PredictionResultView(APIView):
    def get(self, request, ct_id):
        prediction = get_object_or_404(
            Prediction,
            case__ct_id=ct_id,
        )

        if prediction.status != Prediction.Status.COMPLETED:
            payload = _prediction_status_payload(prediction)
            payload["message"] = "분석이 아직 완료되지 않았습니다."
            return Response(payload, status=status.HTTP_202_ACCEPTED)

        result = prediction.result

        return Response(
            {
                "case_id": prediction.case.ct_id,
                "job_id": str(prediction.job_id),
                "status": prediction.status,
                "progress": prediction.progress,
                "elapsed_time": prediction.elapsed_time,
                "original_nifti_url": _artifact_url(
                    request, prediction, "original"
                ),
                "mask_nifti_url": _artifact_url(
                    request, prediction, "mask"
                ),
                "result_json_uri": _optional_artifact_url(
                    request, prediction, "result", result.result_json_uri
                ),
                "preview_image_url": _optional_artifact_url(
                    request, prediction, "preview", result.preview_uri
                ),
                "probability_uri": _optional_artifact_url(
                    request, prediction, "probability", result.probability_uri
                ),
                "entropy_uri": _optional_artifact_url(
                    request, prediction, "entropy", result.entropy_uri
                ),
                "uncertainty_uri": _optional_artifact_url(
                    request, prediction, "uncertainty", result.uncertainty_uri
                ),
                "lesion_volume_ml": result.lesion_volume_ml,
                "lesion_slice_count": result.lesion_slice_count,
                "lesion_slice_start": result.lesion_slice_start,
                "lesion_slice_end": result.lesion_slice_end,
                "max_lesion_slice": result.max_lesion_slice,
                "model_id": result.model_id,
                "model_version": result.model_version,
                "folds": result.folds,
                "checkpoint": result.checkpoint,
                "inference_time_seconds": (
                    result.inference_time_seconds
                ),
                "gpu_peak_memory_mb": result.gpu_peak_memory_mb,
                "error_message": None,
                "message": result.message,
                "created_at": result.created_at,
                "updated_at": prediction.updated_at,
            }
        )


class PredictionArtifactView(APIView):
    def get(self, request, ct_id, artifact):
        prediction = get_object_or_404(
            Prediction.objects.select_related("case", "result"),
            case__ct_id=ct_id,
        )
        object_name = _artifact_object_name(prediction, artifact)
        bucket = storage.Client().bucket(settings.GS_BUCKET_NAME)
        blob = bucket.blob(object_name)

        try:
            stream = blob.open("rb")
        except NotFound as exc:
            raise Http404("Artifact object not found.") from exc

        filename = PurePosixPath(object_name).name
        content_type = (
            blob.content_type
            or mimetypes.guess_type(filename)[0]
            or "application/octet-stream"
        )
        as_attachment = request.query_params.get("download") == "1"
        return FileResponse(
            stream,
            as_attachment=as_attachment,
            filename=filename,
            content_type=content_type,
        )


class PredictionHistoryView(APIView):
    def get(self, request):
        predictions = Prediction.objects.select_related("case").order_by(
            "-case__created_at"
        )

        history = [
            {
                "case_id": prediction.case.ct_id,
                "job_id": str(prediction.job_id),
                "status": prediction.status,
                "progress": prediction.progress,
                "elapsed_time": prediction.elapsed_time,
                "created_at": prediction.case.created_at,
                "updated_at": prediction.updated_at,
                "error_message": prediction.error_message or None,
                "result_available": hasattr(prediction, "result"),
            }
            for prediction in predictions
        ]

        return Response(
            {
                "count": len(history),
                "results": history,
            }
        )
