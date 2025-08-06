from django.urls import path
from .views import Register , SignIn , Logout

urlpatterns = [
    path("register/",Register.as_view(),name="register"),
    path("login/",SignIn.as_view(),name="login"),
    path("logout/",Logout.as_view(),name="logout"),

                ]