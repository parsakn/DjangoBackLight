from django.contrib import admin
from .models import Lamp , LampSchedul  , Room , Home
# Register your models here.
admin.site.register(Lamp)
admin.site.register(LampSchedul)

admin.site.register(Room)
admin.site.register(Home)