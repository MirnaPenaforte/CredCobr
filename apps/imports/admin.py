from django.contrib import admin

from .models import ImportBatch, ImportRejection


admin.site.register(ImportBatch)
admin.site.register(ImportRejection)
