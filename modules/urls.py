from django.urls import path

from .views import delete_module


urlpatterns = [
    path("delete/<uuid:module_id>/", delete_module, name="delete_module"),
]
