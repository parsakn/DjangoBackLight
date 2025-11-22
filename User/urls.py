from django.urls import path
from .views import Register , SignIn , Logout
from .ApiView import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 
urlpatterns = [
    #path("register/",Register.as_view(),name="register"),
    path("register/" ,RegisterView.as_view() , name="register" ),
    # path("login/",SignIn.as_view(),name="login"),
    # path("logout/",Logout.as_view(),name="logout"),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    

                ]