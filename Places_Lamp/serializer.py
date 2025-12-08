from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import * 
from django.db.models import Q
from drf_spectacular.utils import extend_schema_field

@extend_schema_field(serializers.IntegerField)
class UsernameToPkField(serializers.Field) : 
    # the data is just string that determin the username
    def to_internal_value(self, data):
        try : 
            user = get_user_model().objects.get(username = data)
            return user.id
        except : 
            raise serializers.ValidationError("user with specified user name does not exist")

class HomePostSerializer(ModelSerializer) : 
    shared_with_id = serializers.ListField(write_only=True , child = UsernameToPkField(), required=False)
    class Meta : 
        model = Home
        fields = ["id","name", "shared_with_id"]



class HomeViewSerializer(ModelSerializer) : 
    shared_with = serializers.SlugRelatedField(many=True , slug_field = "username" ,read_only=True )
    owner_username = serializers.CharField(source="owner.username" , read_only=True)
    class Meta : 
        model = Home
        fields = ["id","name","owner_username", "shared_with"]

class RoomPostSerializer(ModelSerializer) : 
    home = serializers.PrimaryKeyRelatedField(queryset=Home.objects.all())
    class Meta : 
        model = Room
        fields = ["id","name" , "home"]
    def __init__(self , *args , **kwargs) :
        super().__init__( *args , **kwargs) 
        
        request = self.context["request"]
        if (request and request.user.is_authenticated) : 
            user = request.user
            self.fields["home"].queryset = Home.objects.filter(owner=user)

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
    shared_with_id = serializers.ListField(write_only=True , child = UsernameToPkField(), required=False)
    class Meta : 
        model = Lamp 
        fields =["id","name" , "status" , "room" ,"shared_with_id" ]

    def __init__(self , *args , **kwargs) :
        super().__init__( *args , **kwargs) 
        
        request = self.context["request"]
        if (request and request.user.is_authenticated) : 
            user = request.user
            self.fields["room"].queryset = Room.objects.filter(home__owner=user)
    


class LampPostSchedulSerializer(ModelSerializer) : 
    user_schedul = serializers.PrimaryKeyRelatedField(queryset = UserSchedule.objects.all() , write_only = True)
    lamp = serializers.PrimaryKeyRelatedField(queryset=Lamp.objects.all() , write_only=True)
    class Meta : 
        model=LampSchedul 
        fields ="__all__"
    def __init__(self , *args , **kwargs) :
        super().__init__( *args , **kwargs) 
        
        request = self.context["request"]
        if (request and request.user.is_authenticated) : 
            user = request.user
            self.fields["user_schedul"].queryset = UserSchedule.objects.filter(owner=user)
            self.fields["lamp"].queryset = Lamp.objects.filter(
                Q(room__home__owner=user) | 
                Q(shared_with = user)
            ).distinct()


class LampViewSchedulSerializer(ModelSerializer) : 
    class Meta : 
        model=LampSchedul 
        fields ="__all__"

class UserSchedulPost(ModelSerializer) : 
    class Meta  : 
        model = UserSchedule
        fields = ["id" , "on_time" , "off_time"]
class UserSchedulView(ModelSerializer) : 
    class Meta : 
        models = UserSchedule
        fields = "__all__"
