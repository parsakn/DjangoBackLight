from django.shortcuts import render, redirect
from django.views import View

class ViewHome(View) : 
    def get(self,request) :
        return render(request , "SmartLight/homepage.html")

 
