from django import forms
from .models import Home, Room, Lamp , Place , LampSchedule
from django.forms import DateTimeInput

class PlaceForm(forms.ModelForm):
    class Meta : 
        model = Place
        fields = ["name"]
    # def __init__(self, *args, **kwargs):
    #     user = kwargs.pop('user', None)  
    #     super().__init__(*args, **kwargs)

    #     if user is not None:
    #         self.fields['owner'].queryset = Place.objects.filter(place__owner=user)
    

class HomeForm(forms.ModelForm):
    class Meta:
        model = Home
        fields = ['name', 'place']
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields['place'].queryset = Place.objects.filter(owner=user)

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'home']
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields['home'].queryset = Home.objects.filter(place__owner=user)

class LampForm(forms.ModelForm):
    class Meta:
        model = Lamp
        fields = ['name', 'room', 'status']
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields['room'].queryset = Room.objects.filter(home__place__owner=user)

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
            self.fields['lamp'].queryset = Lamp.objects.filter(room__home__place__owner=user)

