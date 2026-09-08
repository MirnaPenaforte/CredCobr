from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("collections", "0002_collectionstatus_broken_promise")]

    operations = [
        migrations.AddField(
            model_name="paymentagreement",
            name="is_total_value",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="paymentpromise",
            name="is_total_value",
            field=models.BooleanField(default=False),
        ),
    ]
