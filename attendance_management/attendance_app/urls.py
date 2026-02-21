from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home, name="home_page"),
    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register"),
]