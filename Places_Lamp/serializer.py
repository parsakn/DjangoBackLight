from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework import viewsets
from django.contrib.auth import get_user_model
from .models import * 
class UsernameToPkField(serializers.Field) : 
    # the data is just string that determin the username
    def to_internal_value(self, data):
        try : 
            user = get_user_model().objects.filter(username = data)
            return user.id
        except : 
            raise serializers.ValidationError("user with specified user name does not exist")

class HomePostSerializer(ModelSerializer) : 
    shared_with_id = serializers.ListField(write_only=True , child = UsernameToPkField, required=False)
    class Meta : 
        model = Home
        fields = ["id","name", "shared_with_id"]



class HomeViewSerializer(ModelSerializer) : 
    shared_with = serializers.SlugRelatedField(many=True , slug_field = "shared_with" ,read_only=True )
    owner_username = serializers.CharField(source="owner.username" , read_only=True)
    class Meta : 
        model = Home
        fields = ["id","name","owner_username", "shared_with"]

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
    room = serializers.CharField(source = "room.name" , read_only=True)
    shared_with = serializers.SlugRelatedField(many=True , slug_field = "username" ,read_only=True )
    class Meta : 
        model = Lamp 
        fields ="__all__"




class LampPostSerializer(ModelSerializer) : 
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(),write_only=True)
    shared_with_id = serializers.ListField(write_only=True , child = UsernameToPkField, required=False)
    class Meta : 
        model = Lamp 
        fields =["id","name" , "status" , "room" ,"shared_with_id" ]


class LampPostSchedulSerializer(ModelSerializer) : 
    user_schedul = serializers.PrimaryKeyRelatedField(queryset = UserSchedule.objects.all() , write_only = True)
    lamp = serializers.PrimaryKeyRelatedField(queryset=Lamp.objects.all() , write_only=True)
    class Meta : 
        model=LampSchedul 
        fields ="__all__"

class LampViewSchedulSerializer(ModelSerializer) : 
    class Meta : 
        model=LampSchedul 
        fields ="__all__"