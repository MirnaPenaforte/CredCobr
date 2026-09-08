from django.contrib import admin

from .models import AgreementInstallment, CollectionInteraction, CollectionStatus, PaymentAgreement, PaymentPromise

admin.site.register([AgreementInstallment, CollectionInteraction, CollectionStatus, PaymentAgreement, PaymentPromise])
