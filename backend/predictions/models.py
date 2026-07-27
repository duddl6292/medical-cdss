from django.db import models
import uuid
from cases.models import Case


class Prediction(models.Model):
    class Status(models.TextChoices):
        WAITING = "waiting", "대기"
        PROCESSING = "processing", "분석 중"
        COMPLETED = "completed", "완료"
        FAILED = "failed", "실패"
        
    job_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name="prediction",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
    )

    progress = models.PositiveSmallIntegerField(
        default=0,
    )

    elapsed_time = models.FloatField(
        default=0.0,
    )

    error_code = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "AI 분석 작업"
        verbose_name_plural = "AI 분석 작업"

    def __str__(self):
        return f"CT {self.case.ct_id} - {self.status}"
    
class PredictionResult(models.Model):
    prediction = models.OneToOneField(
        Prediction,
        on_delete=models.CASCADE,
        related_name="result",
    )

    # 사용 모델 정보
    model_id = models.CharField(max_length=100)
    model_version = models.CharField(max_length=50)
    folds = models.JSONField(default=list)
    checkpoint = models.CharField(max_length=255)

    # 분석 결과
    mask_path = models.CharField(max_length=500)
    result_json_uri = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )
    preview_uri = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )
    probability_uri = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )
    entropy_uri = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )
    uncertainty_uri = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )
    lesion_volume_ml = models.FloatField(default=0.0)
    lesion_slice_count = models.PositiveIntegerField(default=0)

    # 병변이 없으면 슬라이스 번호가 없을 수 있으므로 null 허용
    lesion_slice_start = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    lesion_slice_end = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    max_lesion_slice = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    # 성능 정보
    inference_time_seconds = models.FloatField(default=0.0)
    gpu_peak_memory_mb = models.FloatField(
        null=True,
        blank=True,
    )

    message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AI 분석 결과"
        verbose_name_plural = "AI 분석 결과"

    def __str__(self):
        return f"분석 결과 - {self.prediction.job_id}"
