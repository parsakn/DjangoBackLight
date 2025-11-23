from rest_framework.generics import CreateAPIView , ListAPIView , ListCreateAPIView
from .serializer import * 
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

class ViewHome(ListAPIView) : 
    def get_queryset(self):
        user = self.request.user
        return Home.objects.filter(owner = user)
    permission_classes = [IsAuthenticated]
    serializer_class = HomeViewSerializer

class PostHome(CreateAPIView) : 
    queryset = Home.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = HomePostSerializer
    def perform_create(self , serializer) : 
        return serializer.save(owner = self.request.user)

class ListRoom(ListAPIView) : 
    def get_queryset(self):
        user = self.request.user
        return Room.objects.filter(owner = user)
    permission_classes = [IsAuthenticated]
    serializer_class = RoomVIewSerializer

class PostRoom(CreateAPIView) : 
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = RoomPostSerializer

class LampView(ListAPIView) : 
    def get_queryset(self):
        user = self.request.user
        return Lamp.objects.filter(
            Q(room__home__owner = user) |
            Q(shared_with = user)
                            )
    permission_classes = [IsAuthenticated]
    serializer_class = LampViewSerializer

class LampCreate(CreateAPIView) : 
    def get_queryset(self):
        user = self.request.user
        return Lamp.objects.filter(owner = user)
    permission_classes = [IsAuthenticated]
    serializer_class = LampPostSerializer

class LampSchedul(ListCreateAPIView) : 
    queryset = LampSchedule.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = LampSchedulSerializer

