from django.db import models

from shared.models import TimestampedModel


class State(TimestampedModel):
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=80)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class EconomicGroup(TimestampedModel):
    name = models.CharField(max_length=160, unique=True)
    source_code = models.CharField(max_length=40, blank=True)

    def __str__(self) -> str:
        return self.name


class Company(TimestampedModel):
    name = models.CharField(max_length=160)
    tax_id = models.CharField(max_length=18, blank=True)
    source_code = models.CharField(max_length=40, blank=True)
    origin_code = models.CharField(max_length=40, blank=True)
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="companies")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["state", "name"], name="unique_company_per_state")]
        indexes = [models.Index(fields=["state", "name"])]
        ordering = ["state__code", "name"]

    def __str__(self) -> str:
        return self.name
