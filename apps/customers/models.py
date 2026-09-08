from django.db import models

from shared.models import TimestampedModel


class Customer(TimestampedModel):
    identifier = models.CharField(max_length=80, unique=True)
    document = models.CharField(max_length=18, blank=True)
    name = models.CharField(max_length=180)
    city = models.CharField(max_length=120, blank=True)
    economic_group = models.ForeignKey(
        "companies.EconomicGroup",
        on_delete=models.PROTECT,
        related_name="customers",
        null=True,
        blank=True,
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    class Meta:
        indexes = [models.Index(fields=["name"]), models.Index(fields=["document"])]

    def __str__(self) -> str:
        return self.name
