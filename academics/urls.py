from django.urls import path
from .views import create_academic_year, delete_academic_year, create_quarter

urlpatterns = [
    path("academic-year/create/", create_academic_year, name="create_academic_year"),
    path("academic-year/delete/<uuid:year_id>/", delete_academic_year, name="delete_academic_year"),
    path("quarter/create/", create_quarter, name="create_quarter"),
]
