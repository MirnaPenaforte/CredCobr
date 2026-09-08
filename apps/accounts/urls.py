from django.urls import path

from . import views


urlpatterns = [
    path("users/", views.user_list, name="user-list"),
    path("users/new/", views.user_create, name="user-create"),
    path("users/<int:pk>/edit/", views.user_update, name="user-update"),
    path("users/<int:pk>/password/", views.user_password, name="user-password"),
    path("users/<int:pk>/toggle-active/", views.user_toggle_active, name="user-toggle-active"),
    path("users/<int:pk>/delete/", views.user_delete, name="user-delete"),
]
