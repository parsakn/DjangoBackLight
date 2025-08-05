from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from . import forms
from django.views import View
from django.contrib.auth.decorators import login_required

class Register(View):
    def get(self, request):
        form = forms.RegistrationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = forms.RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        return render(request, 'register.html', {'form': form})

class SignIn(View):
    def get(self, request):
        form = forms.LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = forms.LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        return render(request, 'login.html', {'form': form})

@login_required(login_url="logout")
class Logout(View):
    def get(self, request):
        logout(request)
        return redirect('login')