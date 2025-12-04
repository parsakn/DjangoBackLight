from django import forms
from .models import Home, Room, Lamp  , LampSchedul
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
    user_ids_to_share = forms.CharField(
        label="User IDs (separate with commas)",
        required=False,
    )

    class Meta:
        model = Lamp
        fields = ['name', 'room', 'status']
    def __init__(self, *args, **kwargs):
        #LampForm(data=request.POST, user=request.user)
        user = kwargs.pop('user', None) # we requier LampForm to get a user in addition 
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields['room'].queryset = Room.objects.filter(home__owner=user)
            # modifiy dropdown of room to only room allowed if room owned by user
    def save(self, commit=True):
        # 1. Save the Lamp instance first
        lamp = super().save(commit=True)

        # 2. Get the IDs entered by the user
        id_string = self.cleaned_data.get('user_ids_to_share', '')
        
        # 3. Convert the string into a list of valid integers
        user_ids = []
        try:
            # Split the string by commas, remove whitespace, and filter out empty entries
            raw_ids = [i.strip() for i in id_string.split(',') if i.strip()]
            user_ids = [int(i) for i in raw_ids]
        except ValueError:
            # Handle error if non-integer data is entered
            # You might want to add a custom form validation error here
            pass

        # 4. Use the .set() method to update the ManyToManyField
        if user_ids:
            # This replaces the existing set of shared users with the new list
            lamp.shared_with.set(user_ids)
        

        return lamp

class LampSchedulForm(forms.ModelForm):
    class Meta:
        model = LampSchedul
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

