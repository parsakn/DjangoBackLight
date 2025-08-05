from django.db import models
from django.contrib.auth import get_user_model
# Create your models here.
class Place(models.Model):
    """
    Place model - represents a location where users can have homes
    """
    name = models.CharField(max_length=128 ,blank=True)
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='places')
    


class Home(models.Model):
    """
    Home model - represents a home within a place
    """
    name = models.CharField(max_length=255 ,blank=True)
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='homes')
    


class Room(models.Model):
    """
    Room model - represents a room within a home
    """
    name = models.CharField(max_length=255 , blank=True)
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name='rooms')
    


class Lamp(models.Model):
    """
    Lamp model - represents a smart lamp in a room
    """
    name = models.CharField(max_length=255)
    status = models.BooleanField(default=False)  # True = on, False = off
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='lamps')
    
    class Meta:
        db_table = 'lamp'
        verbose_name = 'Lamp'
        verbose_name_plural = 'Lamps'
    
    def __str__(self):
        status_text = "ON" if self.status else "OFF"
        return f"{self.name} ({status_text}) in {self.room.name}"
    
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
    
    class Meta:
        db_table = 'lamp_schedule'
        verbose_name = 'Lamp Schedule'
        verbose_name_plural = 'Lamp Schedules'
    
    def __str__(self):
        return f"Schedule for {self.lamp.name}: {self.on_time} - {self.off_time}"
    
    def clean(self):
        """Validate that off_time is after on_time"""
        from django.core.exceptions import ValidationError
        if self.on_time and self.off_time and self.on_time >= self.off_time:
            raise ValidationError("Off time must be after on time")


class StatusLog(models.Model):
    """
    StatusLog model - tracks real-time lamp status changes
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='status_logs')
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name='status_logs')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='status_logs')
    lamp = models.ForeignKey(Lamp, on_delete=models.CASCADE, related_name='status_logs')
    status = models.BooleanField()  # True = on, False = off
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'status_log'
        verbose_name = 'Status Log'
        verbose_name_plural = 'Status Logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        status_text = "ON" if self.status else "OFF"
        return f"{self.lamp.name} {status_text} at {self.timestamp} by {self.user.username}"
    
    @classmethod
    def log_status_change(cls, user, lamp, status, home=None, room=None):
        """
        Create a status log entry for a lamp status change
        """
        if home is None:
            home = lamp.room.home
        if room is None:
            room = lamp.room
        
        return cls.objects.create(
            user=user,
            home=home,
            room=room,
            lamp=lamp,
            status=status
        )