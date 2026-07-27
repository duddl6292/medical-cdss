from django.conf import settings
from django.db import models


class Case(models.Model):
    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "검토 대기"
        REVIEWED = "reviewed", "검토 완료"

    ct_id = models.BigAutoField(primary_key=True)

    ct_file = models.FileField(upload_to="ct_files/")
    subject_id = models.CharField(
        max_length=64,
        db_index=True,
        default="DEMO-UNASSIGNED",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_cdss_cases",
    )
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_cdss_cases",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "CT 검사"
        verbose_name_plural = "CT 검사"

    def __str__(self):
        return f"CT {self.ct_id}"
