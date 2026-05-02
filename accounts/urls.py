from django.urls import path
from .views import (
    add_student_to_module_run,
    delete_user,
    home,
    login_view,
    logout_view,
    module_attendance_panel,
    module_students_panel,
    remove_student_from_module_run,
    save_module_attendance,
)

urlpatterns = [
    path("", login_view, name="login"),
    path("home/", home, name="home"),
    path("logout/", logout_view, name="logout"),
    path("users/delete/<uuid:user_id>/", delete_user, name="delete_user"),
    path("module-runs/<uuid:module_run_id>/students/", module_students_panel, name="module_students_panel"),
    path("module-runs/<uuid:module_run_id>/students/add/", add_student_to_module_run, name="add_student_to_module_run"),
    path(
        "module-runs/<uuid:module_run_id>/students/<uuid:enrollment_id>/remove/",
        remove_student_from_module_run,
        name="remove_student_from_module_run",
    ),
    path("module-runs/<uuid:module_run_id>/attendance/", module_attendance_panel, name="module_attendance_panel"),
    path("module-runs/<uuid:module_run_id>/attendance/save/", save_module_attendance, name="save_module_attendance"),
]
