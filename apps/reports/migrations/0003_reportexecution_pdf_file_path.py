from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("reports", "0002_reportexecution_overdue_band_and_more")]

    operations = [
        migrations.AddField(
            model_name="reportexecution",
            name="pdf_file_path",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
