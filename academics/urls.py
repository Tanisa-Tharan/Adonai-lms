from django.urls import path
from .views import create_academic_year, delete_academic_year

urlpatterns = [
    path("academic-year/create/", create_academic_year, name="create_academic_year"),
    path("academic-year/delete/<uuid:year_id>/", delete_academic_year, name="delete_academic_year"),
]
