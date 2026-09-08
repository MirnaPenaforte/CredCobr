from django.db import migrations, models


def normalize_recipient_profiles(apps, schema_editor):
    Recipient = apps.get_model("notifications", "Recipient")
    Recipient.objects.exclude(profile="administrator").update(profile="manager")


class Migration(migrations.Migration):
    dependencies = [("notifications", "0001_initial")]
    operations = [
        migrations.RunPython(normalize_recipient_profiles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="recipient",
            name="profile",
            field=models.CharField(
                choices=[("administrator", "Administrador"), ("manager", "Gestor")],
                max_length=20,
            ),
        ),
    ]
