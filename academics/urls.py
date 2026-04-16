from django.urls import path
from .views import delete_academic_year

urlpatterns = [
    path("academic-year/delete/<uuid:year_id>/", delete_academic_year, name="delete_academic_year"),
]
