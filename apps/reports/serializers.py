from rest_framework import serializers

from .models import ReportExecution


class ReportExecutionSerializer(serializers.ModelSerializer):
    state = serializers.SlugRelatedField(read_only=True, slug_field="code")
    report_date = serializers.DateField(format="%m/%d/%Y", read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = ReportExecution
        fields = [
            "id", "state", "report_type", "overdue_band", "report_date", "status", "checksum",
            "rows_processed", "error_message", "created_at", "finished_at", "download_url",
        ]

    def get_download_url(self, obj):
        request = self.context.get("request")
        if not request or not obj.file_path or obj.status != ReportExecution.Status.COMPLETED:
            return None
        return request.build_absolute_uri(f"/reports/{obj.pk}/download/")
