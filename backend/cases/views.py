from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from predictions.models import Prediction

from .serializers import CaseUploadSerializer


class PredictView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = CaseUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        case = serializer.save()

        prediction = Prediction.objects.create(
            case=case,
            status=Prediction.Status.WAITING,
            progress=0,
            elapsed_time=0.0,
)

        return Response(
            {
                "ct_id": case.ct_id,
                "job_id": str(prediction.job_id),
                "status": prediction.status,
                "progress": prediction.progress,
                "elapsed_time": prediction.elapsed_time,
            },
            status=status.HTTP_201_CREATED,
)