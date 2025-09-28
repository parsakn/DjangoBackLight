from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import  HomeForm , LampForm ,RoomForm, LampSchedulForm 
# Create your views here.

class SettingsView(LoginRequiredMixin, View):
    template_name = 'Places_Lamp/settings.html'

    def get(self, request):
        return render(request, self.template_name, {
            
            'home_form': HomeForm(),
            'room_form': RoomForm(),
            'lamp_form' : LampForm(),
            'lamp_schedul' : LampSchedulForm(),
            
        })

    def post(self, request):

        home_form = HomeForm()
        room_form = RoomForm(user=request.user)
        lamp_form = LampForm(user=request.user)
        lamp_schedul = LampSchedulForm(user=request.user)



        if 'submit_home' in request.POST:
            home_form = HomeForm(request.POST)
            if home_form.is_valid():
                home=home_form.save(commit=False)
                home.owner = request.user 
                home.save()
                

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
            
            'home_form': home_form,
            'room_form': room_form,
            'lamp_form' : lamp_form,
            'lamp_schedul' : lamp_schedul , 
        })
    
class Profile(LoginRequiredMixin, View) : 
    template_name = 'Places_Lamp/profile.html'

    def get(self, request):
        # lamps owned by user's homes
        owned_homes = request.user.places.all()
        owned_lamps = []
        for home in owned_homes:
            for room in home.rooms.all():
                owned_lamps.extend(list(room.lamps.all()))

        # lamps shared with user
        shared_lamps = request.user.shared_lamps.all()

        # combine and deduplicate by id
        # lamps = {l.id: l for l in (owned_lamps + list(shared_lamps))}.values()
        established_lamps , unestablished_lamps = [] , []
        for lamp in (owned_lamps+list(shared_lamps)) : 
            if lamp.connection == True : 
                established_lamps.append(lamp)
            else : 
                unestablished_lamps.append(lamp)
        
        return render(request, self.template_name, {"established_lamps": established_lamps , "unestablished_lamps" : unestablished_lamps})


