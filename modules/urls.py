from django.urls import path

from .downloads import (
    download_assignment_file,
    download_assignment_submission,
    download_course_material,
)
from .views import delete_module, upload_course_material, delete_course_material


urlpatterns = [
    path("delete/<uuid:module_id>/", delete_module, name="delete_module"),
    path("upload-material/", upload_course_material, name="upload_course_material"),
    path("delete-material/<uuid:material_id>/", delete_course_material, name="module_delete_course_material"),
    path("materials/<uuid:material_id>/download/", download_course_material, name="download_course_material"),
    path("assignment-files/<uuid:file_id>/download/", download_assignment_file, name="download_assignment_file"),
    path("submissions/<uuid:submission_id>/download/", download_assignment_submission, name="download_assignment_submission"),
]
