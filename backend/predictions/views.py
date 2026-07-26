from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Prediction


class PredictionStatusView(APIView):
    def get(self, request, ct_id):
        prediction = get_object_or_404(
            Prediction,
            case__ct_id=ct_id,
        )

        return Response(
            {
                "ct_id": prediction.case.ct_id,
                "job_id": str(prediction.job_id),
                "status": prediction.status,
                "progress": prediction.progress,
                "elapsed_time": prediction.elapsed_time,
            }
        )
        
        
class PredictionResultView(APIView):
    def get(self, request, ct_id):
        prediction = get_object_or_404(
            Prediction,
            case__ct_id=ct_id,
        )

        if prediction.status != Prediction.Status.COMPLETED:
            return Response(
                {
                    "ct_id": prediction.case.ct_id,
                    "job_id": str(prediction.job_id),
                    "status": prediction.status,
                    "progress": prediction.progress,
                    "elapsed_time": prediction.elapsed_time,
                    "message": "분석이 아직 완료되지 않았습니다.",
                },
                status=202,
            )

        result = prediction.result

        return Response(
            {
                "status": "success",
                "model": {
                    "model_id": result.model_id,
                    "model_version": result.model_version,
                    "folds": result.folds,
                    "checkpoint": result.checkpoint,
                },
                "result": {
                    "mask_path": result.mask_path,
                    "lesion_volume_ml": result.lesion_volume_ml,
                    "lesion_slice_count": result.lesion_slice_count,
                    "lesion_slice_start": result.lesion_slice_start,
                    "lesion_slice_end": result.lesion_slice_end,
                    "max_lesion_slice": result.max_lesion_slice,
                },
                "performance": {
                    "inference_time_seconds": result.inference_time_seconds,
                    "gpu_peak_memory_mb": result.gpu_peak_memory_mb,
                },
                "message": result.message,
            }
        )
        
class PredictionHistoryView(APIView):
    def get(self, request):
        predictions = Prediction.objects.select_related("case").order_by(
            "-case__created_at"
        )

        history = [
            {
                "ct_id": prediction.case.ct_id,
                "job_id": str(prediction.job_id),
                "status": prediction.status,
                "progress": prediction.progress,
                "elapsed_time": prediction.elapsed_time,
                "created_at": prediction.case.created_at,
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