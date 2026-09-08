from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


whatsapp_validator = RegexValidator(
    regex=r"^\+[1-9]\d{7,14}$",
    message="Informe o WhatsApp no formato internacional, por exemplo: +5585999999999.",
)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMINISTRATOR = "administrator", "Administrador"
        MANAGER = "manager", "Gestor"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MANAGER)
    whatsapp_number = models.CharField(
        "WhatsApp",
        max_length=16,
        default="",
        validators=[whatsapp_validator],
        help_text="Use o formato internacional com +, código do país e DDD. Ex.: +5585999999999.",
    )

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMINISTRATOR
        self.is_staff = self.role == self.Role.ADMINISTRATOR
        super().save(*args, **kwargs)
