from django.urls import path
from . import views
from . import ApiView
from rest_framework.routers import DefaultRouter
urlpatterns = [
    #path("add/" , views.SettingsView.as_view() , name="add_info") , 
    #path("" , views.Profile.as_view() , name="profile"),
    

]
router = DefaultRouter()

router.register(r"home" , ApiView.HomeHandller , basename="homeH" , )
router.register(r"room" , ApiView.RoomHandller , basename="roomH" , )
router.register(r"lamp" , ApiView.LampHandeller , basename="lampH" ,)
router.register(r"lamp_schedul" , ApiView.LampSchedulHandeller , basename="lampschedulH" )
router.register(r"user_schedul" , ApiView.UserSchedulLampHandeller , basename="userschedulH" )
urlpatterns += router.urls
