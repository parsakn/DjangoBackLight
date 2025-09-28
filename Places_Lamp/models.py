from django.db import models
from django.contrib.auth import get_user_model
from SmartLight import settings
import uuid
# Create your models here.
class Home(models.Model):
    """
    Place model - represents a location where users can have homes
    """
    name = models.CharField(max_length=128 , unique=True )
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='places')
    shared_with = models.ManyToManyField(
        get_user_model(),
        blank=True,
        related_name="shared_homes",
    )

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
    connection = models.BooleanField(default=False) # connection is false until we recive msg ESP connected
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='lamps')
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="shared_lamps"
    )# we can have multy access
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  # 🔒 secret key

    class Meta:
        unique_together = ("room", "name")  # avoid global uniqueness clash

    @property
    def owners(self):
        
        return [self.room.home.owner] + list(self.shared_with.all())

    def __str__(self) : 
        return self.name
    
    def can_access(self, user):
        return (
            user == self.room.home.owner
            or user in self.shared_with.all()
            or user in self.room.home.shared_with.all()
        )


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


