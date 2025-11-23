from django.urls import path
from . import views
from . import ApiView
urlpatterns = [
    #path("add/" , views.SettingsView.as_view() , name="add_info") , 
    #path("" , views.Profile.as_view() , name="profile"),
    path("" ,ApiView.LampView.as_view() , name="profile" ),
    path("add/home" , ApiView.PostHome.as_view() , name="add_home"),
    path("add/room" , ApiView.PostRoom.as_view() , name="add_room"),
    path("add/lamp" , ApiView.LampCreate.as_view() , name="add_lamp"),
]
