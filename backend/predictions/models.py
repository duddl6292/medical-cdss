from django.db import models

from cases.models import Case


class Prediction(models.Model):
    class Status(models.TextChoices):
        WAITING = "waiting", "대기 중"
        PROCESSING = "processing", "분석 중"
        COMPLETED = "completed", "분석 완료"
        FAILED = "failed", "분석 실패"

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

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"CT {self.case.ct_id} - {self.status}"