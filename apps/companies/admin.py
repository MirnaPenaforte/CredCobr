from django.contrib import admin

from .models import Company, EconomicGroup, State

admin.site.register([Company, EconomicGroup, State])
