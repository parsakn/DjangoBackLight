from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import * 

class HomePostSerializer(ModelSerializer) : 
    shared_with = serializers.PrimaryKeyRelatedField(queryset= get_user_model().objects.all() , many = True , required=False)
    class Meta : 
        model = Home
        fields = ["id","name", "shared_with"]



class HomeViewSerializer(ModelSerializer) : 
    shared_with = serializers.SlugRelatedField(many=True , slug_field = "shared_with" ,read_only=True )
    owner = serializers.CharField(source="owner.username")
    class Meta : 
        model = Home
        fields = ["id","name","owner", "shared_with"]

class RoomPostSerializer(ModelSerializer) : 
    home = serializers.PrimaryKeyRelatedField(queryset=Home.objects.all())
    class Meta : 
        model = Room
        fields = ["id","name" , "home"]

class RoomVIewSerializer(ModelSerializer) : 
    home = serializers.CharField(source = "home.name")
    class Meta : 
        model = Room
        fields = ["id","name" , "home"]

class LampViewSerializer(ModelSerializer) : 
    room = serializers.CharField(source = "room.name")
    shared_with = serializers.SlugRelatedField(many=True , slug_field = "username" ,read_only=True )
    class Meta : 
        model = Lamp 
        fields ="__all__"

class LampPostSerializer(ModelSerializer) : 
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
    shared_with = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all() , many=True , required=False)
    class Meta : 
        model = Lamp 
        fields =["id","name" , "status" , "room" , "shared_with" , ]
class LampSchedulSerializer(ModelSerializer) : 
    class Meta : 
        model=LampSchedule 
        fields ="__all__"



