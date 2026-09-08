from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("collections", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="collectionstatus",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pendente"), ("contacted", "Contactado"),
                    ("promise", "Promessa registrada"), ("negotiating", "Em negociacao"),
                    ("paid", "Pago"), ("unreachable", "Nao localizado"),
                    ("broken_promise", "Promessa não cumprida"),
                ],
                default="pending", max_length=20,
            ),
        ),
    ]
