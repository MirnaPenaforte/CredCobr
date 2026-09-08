from rest_framework import serializers

from .models import ImportBatch


class ImportBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportBatch
        fields = [
            "id", "source", "status", "file_name", "total_rows", "imported_rows",
            "rejected_rows", "error_message", "started_at", "finished_at", "created_at",
        ]
        read_only_fields = fields


class ExcelImportSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.lower().endswith(".xlsx"):
            raise serializers.ValidationError("Somente arquivos .xlsx são aceitos.")
        return value
