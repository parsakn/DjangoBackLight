from rest_framework.serializers import ModelSerializer
from .models import * 

class HomeSerializer(ModelSerializer) : 
    class Meta : 
        models = Home
        fields = ["name" , "owner" , "shared_with"]

class RoomSerializer(ModelSerializer) : 
    class Meta : 
        models = Room
        fields = ["name" , "home"]

class LampViewSerializer(ModelSerializer) : 
    class Meta : 
        models = Lamp 
        fields ="__all__"

class LampPostSerializer(ModelSerializer) : 
    class Meta : 
        models = Lamp 
        fields =["name" , "status" , "room" , "shared_with" , ]
class LampSchedulSerializer(ModelSerializer) : 
    class Meta : 
        models=LampSchedule 
        fields ="__all__"

