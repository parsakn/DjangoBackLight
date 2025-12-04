from rest_framework import serializers
from .models import CustomeUser 
from django.contrib.auth.password_validation import validate_password
class UserCreateSerializer(serializers.ModelSerializer) : 

    password2 = serializers.CharField(write_only=True , required=True , validators=[validate_password])

    def create(self , validated_data):
        del validated_data["password2"]
        user = CustomeUser.objects.create(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user




    class Meta:
        model = CustomeUser
        fields=["username" , "email" , "password","password2" , "phone_number"]
    def validate(self, attrs):
        if attrs["password"] != attrs["password2"] : 
            raise serializers.ValidationError({"password":"password does not matched"})
        return attrs
    