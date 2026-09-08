from django.contrib import admin

from .models import Notification, Recipient

admin.site.register([Notification, Recipient])
