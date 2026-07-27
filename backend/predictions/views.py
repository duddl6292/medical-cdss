from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Prediction
from .services import PredictionDispatchError, dispatch_prediction


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
                "original_nifti_url": prediction.case.ct_file.url,
                "mask_nifti_url": result.mask_path,
                "result_json_uri": result.result_json_uri,
                "preview_image_url": result.preview_uri or None,
                "probability_uri": result.probability_uri or None,
                "entropy_uri": result.entropy_uri or None,
                "uncertainty_uri": result.uncertainty_uri or None,
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
