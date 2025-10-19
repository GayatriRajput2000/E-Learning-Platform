from django.urls import path
from accounts import views

urlpatterns = [
    path("login/", views.custom_login, name="login"),
    path("register/", views.custom_register, name="register"),
    path("logout/", views.custom_logout, name="logout"),
]
