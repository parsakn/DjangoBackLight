from rest_framework.generics import CreateAPIView , ListAPIView , ListCreateAPIView
from .serializer import * 
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework import viewsets

class HomeHandller(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'head', 'options']
    queryset = Home.objects.all()
    def get_queryset(self):
        user = self.request.user
        return Home.objects.filter(owner=user)
    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return HomeViewSerializer
        elif self.action in ["create", "update", "partial_update"] : 
            return HomePostSerializer
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    permission_classes = [IsAuthenticated]

# class ListRoom(ListAPIView) : 
#     def get_queryset(self):
#         user = self.request.user
#         return Room.objects.filter(owner = user)
#     permission_classes = [IsAuthenticated]
#     serializer_class = RoomVIewSerializer

# class PostRoom(CreateAPIView) : 
#     queryset = Room.objects.all()
#     permission_classes = [IsAuthenticated]
#     serializer_class = RoomPostSerializer

class RoomHandller(viewsets.ModelViewSet) : 
    queryset = Room.objects.all()
    http_method_names = ['get', 'post', 'head', 'options']
    def get_queryset(self):
        user = self.request.user
        return Room.objects.filter(owner = user)
    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RoomVIewSerializer
        elif self.action in ["create", "update", "partial_update"] : 
            return RoomPostSerializer
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
    permission_classes = [IsAuthenticated]
    

# class LampView(ListAPIView) : 
#     def get_queryset(self):
#         user = self.request.user
#         return Lamp.objects.filter(
#             Q(room__home__owner = user) |
#             Q(shared_with = user)
#                             )
#     permission_classes = [IsAuthenticated]
#     serializer_class = LampViewSerializer

# class LampCreate(CreateAPIView) : 
#     queryset = Lamp.objects.all()
#     permission_classes = [IsAuthenticated]
#     serializer_class = LampPostSerializer

class LampHandeller(viewsets.ModelViewSet) :
    queryset = Lamp.objects.all() 
    http_method_names = ['get', 'post', 'head', 'options']
    def get_queryset(self):
        user = self.request.user
        return Lamp.objects.filter(
            Q(room__home__owner = user) |
            Q(shared_with = user)
                            ).distinct()
    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return LampViewSerializer
        elif self.action in ["create", "update", "partial_update"] : 
            return LampPostSerializer
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
    permission_classes=[IsAuthenticated]

class LampSchedulHandeller(viewsets.ModelViewSet) : 
    queryset = LampSchedul.objects.all()
    http_method_names = ['get', 'post', 'head', 'options']
    def get_queryset(self):
        # it does only effect on GET and not POST requests
        user = self.request.user
        return LampSchedul.objects.filter(user_schedul__owner=user)
    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return LampViewSchedulSerializer
        elif self.action in ["create", "update", "partial_update"] : 
            return LampPostSchedulSerializer
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
    permission_classes = [IsAuthenticated]
