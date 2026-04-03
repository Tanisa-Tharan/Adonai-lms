from django.urls import path
from .views import delete_user, login_view, dashboard, create_user, logout_view

urlpatterns = [
    path("", login_view, name="login"),
    path("dashboard/", dashboard, name="dashboard"),
    path("users/create/", create_user, name="create_user"),
    path("logout/", logout_view, name="logout"),
    path("users/delete/<uuid:user_id>/", delete_user, name="delete_user"),
]
