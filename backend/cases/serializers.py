from django.conf import settings
from rest_framework import serializers

from .models import Case


class CaseUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["ct_id", "subject_id", "ct_file"]
        read_only_fields = ["ct_id"]

    def validate_subject_id(self, value):
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError(
                "비식별 대상자 ID를 입력해 주세요."
            )
        return normalized

    def validate_ct_file(self, file):
        if not file.name.lower().endswith((".nii", ".nii.gz")):
            raise serializers.ValidationError(
                "CT 파일은 .nii 또는 .nii.gz 형식만 업로드할 수 있습니다."
            )
        if file.size <= 0:
            raise serializers.ValidationError(
                "빈 파일은 업로드할 수 없습니다."
            )
        if file.size > settings.MAX_NIFTI_UPLOAD_BYTES:
            raise serializers.ValidationError(
                "업로드 파일이 허용된 크기를 초과했습니다."
            )
        return file
