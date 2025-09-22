from django.urls import path
from . import views
urlpatterns = [
    path("add/" , views.SettingsView.as_view() , name="add_info") , 
    path("" , views.Profile.as_view() , name="profile"),
]
