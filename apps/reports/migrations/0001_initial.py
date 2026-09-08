import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("companies", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="ReportExecution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("report_type", models.CharField(choices=[("state_excel", "Excel estadual"), ("executive_pdf", "PDF executivo")], default="state_excel", max_length=30)),
                ("report_date", models.DateField()),
                ("status", models.CharField(choices=[("pending", "Pendente"), ("processing", "Processando"), ("completed", "Concluído"), ("failed", "Falhou")], default="pending", max_length=20)),
                ("file_path", models.CharField(blank=True, max_length=500)),
                ("checksum", models.CharField(blank=True, max_length=64)),
                ("rows_processed", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("state", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="companies.state")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="reportexecution", index=models.Index(fields=["report_date", "status", "report_type"], name="reports_rep_report__801238_idx")),
    ]
