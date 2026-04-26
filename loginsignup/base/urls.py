from django.urls import path, include
from .views import authView, home, loginView, logoutView, aboutus, profile, edit_profile

app_name = "base"

urlpatterns = [
    path("", home, name="home"),
    path("signup/", authView, name="authView"),
    path("login/", loginView, name="login"),
    path("logout/", logoutView, name="logout"),
    path('aboutus/', aboutus, name='aboutus'),
    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'), 
]