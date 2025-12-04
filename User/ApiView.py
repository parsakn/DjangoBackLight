from rest_framework import generics
from .models import CustomeUser
from .serializer import UserCreateSerializer
from rest_framework.permissions import AllowAny

class RegisterView(generics.CreateAPIView):
    queryset = CustomeUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserCreateSerializer