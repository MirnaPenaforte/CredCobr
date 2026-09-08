import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="ImportBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source", models.CharField(choices=[("excel", "Excel"), ("legacy", "Banco legado"), ("itecnove", "BI Itecnove")], max_length=20)),
                ("status", models.CharField(choices=[("pending", "Pendente"), ("processing", "Processando"), ("completed", "Concluído"), ("failed", "Falhou")], default="pending", max_length=20)),
                ("file_name", models.CharField(blank=True, max_length=255)),
                ("total_rows", models.PositiveIntegerField(default=0)),
                ("imported_rows", models.PositiveIntegerField(default=0)),
                ("rejected_rows", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="import_batches", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ImportRejection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("row_number", models.PositiveIntegerField()),
                ("reason", models.TextField()),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="rejections", to="imports.importbatch")),
            ],
            options={"ordering": ["row_number"]},
        ),
        migrations.AddIndex(model_name="importbatch", index=models.Index(fields=["source", "status", "created_at"], name="imports_imp_source_7a540e_idx")),
    ]
