from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reports", "0004_alter_reportexecution_report_type")]

    operations = [
        migrations.AlterField(
            model_name="reportexecution",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pendente"),
                    ("processing", "Processando"),
                    ("completed", "Concluído"),
                    ("superseded", "Substituído"),
                    ("failed", "Falhou"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
