from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from . import forms
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator

class Register(View):
    def get(self, request):
        form = forms.RegistrationForm()
        return render(request, 'User/register.html', {'form': form})

    def post(self, request):
        form = forms.RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request , "Success Registration")
            return redirect('login')
        else :
            messages.error(request , "Failure Registration")
            return render(request, 'User/register.html', {'form': form})

class SignIn(View):
    def get(self, request):
        form = forms.LoginForm()
        return render(request, 'User/login.html', {'form': form})

    def post(self, request):
        form = forms.LoginForm(request, data=request.POST)
        if form.is_valid():
            
            user = form.get_user()
            login(request, user)
            messages.success(request , "Success Signin")
            return redirect('home')
        else : 
            messages.error(request , "Failure Signin")
            return render(request, 'User/login.html', {'form': form})

@method_decorator(login_required(login_url='login'), name='dispatch')
class Logout(View):
    def get(self, request):
        logout(request)
        messages.success(request , "Success Logout")
        return redirect('login')