from rest_framework import serializers

from .models import Case


class CaseUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["ct_id", "ct_file"]
        read_only_fields = ["ct_id"]

    def validate_ct_file(self, file):
        if not file.name.endswith(".nii.gz"):
            raise serializers.ValidationError(
                "CT 파일은 .nii.gz 형식만 업로드할 수 있습니다."
            )

        return file