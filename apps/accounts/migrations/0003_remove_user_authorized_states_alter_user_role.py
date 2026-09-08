from django.db import migrations, models


def normalize_user_roles(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(is_superuser=True).update(role="administrator", is_staff=True)
    User.objects.filter(role="administrator").update(is_staff=True)
    User.objects.exclude(role="administrator").update(role="manager", is_staff=False)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_user_authorized_states")]
    operations = [
        migrations.RunPython(normalize_user_roles, migrations.RunPython.noop),
        migrations.RemoveField(model_name="user", name="authorized_states"),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[("administrator", "Administrador"), ("manager", "Gestor")],
                default="manager",
                max_length=20,
            ),
        ),
    ]
