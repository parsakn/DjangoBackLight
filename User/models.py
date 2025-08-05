from django.db import models
from django.contrib.auth.models import  AbstractUser 

class CustomeUser (AbstractUser) : 
    username = models.CharField(max_length=128) 
    email = models.EmailField(max_length=128)
    password = models.CharField(max_length=128)
    is_service_provider = models.BooleanField()


