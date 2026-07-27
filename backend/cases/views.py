from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from predictions.models import Prediction
from common.models import AuditEvent

from .serializers import CaseUploadSerializer


class PredictView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = CaseUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        case = serializer.save(uploaded_by=request.user)

        prediction = Prediction.objects.create(
            case=case,
            status=Prediction.Status.WAITING,
            progress=0,
            elapsed_time=0.0,
        )
        AuditEvent.objects.create(
            actor=request.user,
            action="case.upload",
            target_type="case",
            target_id=str(case.ct_id),
            metadata={"subject_id": case.subject_id},
        )

        return Response(
            {
                "case_id": case.ct_id,
                "subject_id": case.subject_id,
                "job_id": str(prediction.job_id),
                "status": prediction.status,
                "progress": prediction.progress,
                "elapsed_time": prediction.elapsed_time,
                "created_at": case.created_at,
            },
            status=status.HTTP_201_CREATED,
        )
