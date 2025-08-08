from django import forms
from .models import Home, Room, Lamp  , LampSchedule
from django.forms import DateTimeInput

class HomeForm(forms.ModelForm):
    class Meta : 
        model = Home
        fields = ["name"]
    # def __init__(self, *args, **kwargs):
    #     user = kwargs.pop('user', None)  
    #     super().__init__(*args, **kwargs)

    #     if user is not None:
    #         self.fields['owner'].queryset = Place.objects.filter(place__owner=user)
    



class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'home']
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields['home'].queryset = Home.objects.filter(owner=user)

class LampForm(forms.ModelForm):
    class Meta:
        model = Lamp
        fields = ['name', 'room', 'status']
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields['room'].queryset = Room.objects.filter(home__owner=user)

class LampSchedulForm(forms.ModelForm):
    class Meta:
        model = LampSchedule
        fields ="__all__"
        widgets = {
            'on_time': DateTimeInput(attrs={'type': 'datetime-local'}),
            'off_time': DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields['lamp'].queryset = Lamp.objects.filter(room__home__owner=user)

