from django.contrib import admin
from .models import Lamp , LampSchedule , Place , Room , Home
# Register your models here.
admin.site.register(Lamp)
admin.site.register(LampSchedule)
admin.site.register(Place)
admin.site.register(Room)
admin.site.register(Home)