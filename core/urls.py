from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.dashboard.urls")),
    path("api/", include("apps.api.urls")),
    path("api/webhooks/", include("apps.notifications.urls")),
]
