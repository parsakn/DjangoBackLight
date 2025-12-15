from rest_framework.generics import CreateAPIView , ListAPIView , ListCreateAPIView
from .serializer import * 
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import paho.mqtt.publish as publish
import json
from SmartLight import settings
import time

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
        # Room has no direct owner field; ownership is via the parent Home.
        return Room.objects.filter(
            Q(home__owner=user) | Q(home__shared_with=user)
        ).distinct()
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
    http_method_names = ['get', 'post', 'head', 'options', 'patch']
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

    @action(detail=True, methods=["patch"], url_path="status")
    def set_status(self, request, pk=None):
        """
        Change lamp on/off status and forward command via existing MQTT bridge.

        Request body: {"status": true} or {"status": false}
        """
        lamp = self.get_object()
        original_status = bool(lamp.status)
        user = request.user

        # Authorization check reuses existing domain rule.
        if not lamp.can_access(user):
            return Response({"detail": "Not allowed to control this lamp."}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get("status", None)
        if not isinstance(new_status, bool):
            return Response(
                {"detail": "Field 'status' must be a boolean."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Map boolean to payload understood by existing consumers / devices.
        payload = "1" if new_status else "0"

        # Publish directly to MQTT broker (same format as MqttConsumer.mqtt_pub)
        topic = f"Devices/{lamp.token}/command"
        dict_payload = {"msg": payload}
        json_payload = json.dumps(dict_payload)
        
        try:
            publish.single(topic, json_payload, hostname=settings.MQTT_BROKER, port=settings.MQTT_PORT)
            print(f"MQTT PUB → {user.username} → {topic}={json_payload}", flush=True)
        except Exception as e:
            # Log error but still return success since DB is updated
            print(f"⚠️ MQTT publish failed: {e}", flush=True)
            return Response(
                {
                    "detail": "Lamp status updated locally but MQTT publish failed.",
                    "error": str(e),
                    "lamp": LampViewSerializer(lamp).data,
                },
                status=status.HTTP_200_OK,
            )

        # Wait up to 5 seconds for the device/MQTT bridge to report the new status.
        # We re-read from the database and compare to the desired status.
        deadline = time.time() + 5.0
        desired_status = bool(new_status)

        while time.time() < deadline:
            time.sleep(0.5)
            # Reload lamp from DB to see if status has changed
            refreshed = Lamp.objects.get(pk=lamp.pk)
            if bool(refreshed.status) == desired_status:
                serializer = LampViewSerializer(refreshed, context=self.get_serializer_context())
                return Response(serializer.data, status=status.HTTP_200_OK)

        # If we reach here, the device never confirmed the status change in time.
        # Treat this as a failure to execute the command.
        current = Lamp.objects.get(pk=lamp.pk)
        serializer = LampViewSerializer(current, context=self.get_serializer_context())
        return Response(
            {
                "detail": "Lamp status command timed out without device confirmation.",
                "lamp": serializer.data,
            },
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )

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

class UserSchedulLampHandeller(viewsets.ModelViewSet) : 
    queryset = LampSchedul.objects.all()
    http_method_names = ['get', 'post', 'head', 'options']
    def get_queryset(self) : 
        user = self.request.user
        return UserSchedule.objects.filter(user_schedul__owner=user)
    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return UserSchedulView
        elif self.action in ["create", "update", "partial_update"] : 
            return UserSchedulPost
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
