from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import PlaceForm , HomeForm , LampForm ,RoomForm, LampSchedulForm 
# Create your views here.

class SettingsView(LoginRequiredMixin, View):
    template_name = 'Places_Lamp/settings.html'

    def get(self, request):
        return render(request, self.template_name, {
            'place_form': PlaceForm(),
            'home_form': HomeForm(),
            'room_form': RoomForm(),
            'lamp_form' : LampForm(),
            'lamp_schedul' : LampSchedulForm(),
            
        })

    def post(self, request):
        place_form = PlaceForm()
        home_form = HomeForm(user=request.user)
        room_form = RoomForm(user=request.user)
        lamp_form = LampForm(user=request.user)
        lamp_schedul = LampSchedulForm(user=request.user)

        if 'submit_place' in request.POST:
            place_form = PlaceForm(request.POST)
            if place_form.is_valid():
                place=place_form.save(commit=False)
                place.owner = request.user
                place.save()
                pass

        elif 'submit_home' in request.POST:
            home_form = HomeForm(request.POST)
            if home_form.is_valid():
                home_form.save()
                

        elif 'submit_room' in request.POST:
            room_form = RoomForm(request.POST)
            if room_form.is_valid():
                room_form.save()

        elif 'submit_schedul' in request.POST:
            lamp_schedul = LampSchedulForm(request.POST)
            if lamp_schedul.is_valid():
                lamp_schedul.save()
        
        elif 'submit_lamp' in request.POST:
            lamp_form = LampForm(request.POST)
            if lamp_form.is_valid():
                lamp_form.save()
        

            
        return render(request, self.template_name, {
            'place_form': place_form,
            'home_form': home_form,
            'room_form': room_form,
            'lamp_form' : lamp_form,
            'lamp_schedul' : lamp_schedul , 
        })
