from django.urls import path

from .views import delete_module, upload_course_material, delete_course_material


urlpatterns = [
    path("delete/<uuid:module_id>/", delete_module, name="delete_module"),
    path("upload-material/", upload_course_material, name="upload_course_material"),
    path("delete-material/<uuid:material_id>/", delete_course_material, name="delete_course_material"),
]
