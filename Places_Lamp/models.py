from django.db import models
from django.contrib.auth import get_user_model
from SmartLight import settings
import uuid
# Create your models here.
class Home(models.Model):
    """
    Home model - represents a location where users can have homes.
    Name should be unique per owner, not globally.
    """
    name = models.CharField(max_length=128)
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='places')
    shared_with = models.ManyToManyField(
        get_user_model(),
        blank=True,
        related_name="shared_homes",
    )

    class Meta:
        # Allow different users to have homes with the same name,
        # but prevent duplicate names for the same owner.
        unique_together = ("owner", "name")

    def __str__(self) : 
        return self.name
    





class Room(models.Model):
    """
    Room model - represents a room within a home
    """
    # Room names should be unique only *within* the same home, not globally.
    # Global uniqueness here prevented creating rooms with the same name
    # in different homes.
    name = models.CharField(max_length=255, blank=True)
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name='rooms')

    class Meta:
        # Enforce "no duplicate room name in the same home", but allow
        # the same room name across different homes.
        unique_together = ("home", "name")

    def __str__(self) : 
        return self.name


class Lamp(models.Model):
    """
    Lamp model - represents a smart lamp in a room
    """
    # Name should not be globally unique; only unique within a room.
    name = models.CharField(max_length=255, blank=True)
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


class UserSchedule(models.Model):

    owner = models.ForeignKey(get_user_model() , models.CASCADE)
    on_time = models.DateTimeField()
    off_time = models.DateTimeField()
    
    
    def clean(self):
        """Validate that off_time is after on_time"""
        from django.core.exceptions import ValidationError
        if self.on_time and self.off_time and self.on_time >= self.off_time:
            raise ValidationError("Off time must be after on time")
        

class LampSchedul(models.Model) : 
    lamp = models.ForeignKey(Lamp , models.CASCADE)
    user_schedul = models.ForeignKey(UserSchedule , models.CASCADE)




