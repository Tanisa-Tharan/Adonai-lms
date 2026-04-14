from django.urls import path
from .views import delete_user, home, login_view, logout_view

urlpatterns = [
    path("", login_view, name="login"),
    path("home/", home, name="home"),
    path("logout/", logout_view, name="logout"),
    path("users/delete/<uuid:user_id>/", delete_user, name="delete_user"),
]
