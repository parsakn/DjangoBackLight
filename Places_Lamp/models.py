from django.db import models
from django.contrib.auth import get_user_model
# Create your models here.
class Home(models.Model):
    """
    Place model - represents a location where users can have homes
    """
    name = models.CharField(max_length=128 , unique=True )
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='places')

    def __str__(self) : 
        return self.name
    





class Room(models.Model):
    """
    Room model - represents a room within a home
    """
    name = models.CharField(max_length=255 , blank=True , unique=True)
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name='rooms')
    def __str__(self) : 
        return self.name


class Lamp(models.Model):
    """
    Lamp model - represents a smart lamp in a room
    """
    name = models.CharField(max_length=255 , blank=True , unique=True)
    status = models.BooleanField(default=False)  # True = on, False = off
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='lamps')
    
    def __str__(self) : 
        return self.name
    
    def toggle_status(self):
        """Toggle the lamp status"""
        self.status = not self.status
        self.save()
        return self.status


class LampSchedule(models.Model):
    """
    LampSchedule model - represents automated schedules for lamps
    """
    lamp = models.ForeignKey(Lamp, on_delete=models.CASCADE, related_name='schedules')
    on_time = models.DateTimeField()
    off_time = models.DateTimeField()
    
    
    def clean(self):
        """Validate that off_time is after on_time"""
        from django.core.exceptions import ValidationError
        if self.on_time and self.off_time and self.on_time >= self.off_time:
            raise ValidationError("Off time must be after on time")


