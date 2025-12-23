from rest_framework.generics import CreateAPIView , ListAPIView , ListCreateAPIView
from .serializer import * 
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from Places_Lamp.services.lamp_control import set_lamp_status
from VoiceAgent.services import exceptions as voice_exceptions

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
        Change lamp on/off status and forward command to the MQTT broker.

        Request body: {"status": true} or {"status": false}

        This view keeps the same external behaviour as before the refactor:
        - 403 when the user cannot control the lamp
        - 400 when the `status` field is invalid
        - 504 when the command times out without device confirmation
        - 200 on success, and also 200 when MQTT publish fails but local state
          is (eventually) updated.
        """
        lamp = self.get_object()
        new_status = request.data.get("status", None)
        if not isinstance(new_status, bool):
            return Response(
                {"detail": "Field 'status' must be a boolean."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Core logic (permissions + MQTT + polling) lives in the shared
            # service so it can be reused by the voice agent.
            set_lamp_status(
                user=request.user,
                lamp=lamp,
                desired_status=bool(new_status),
            )
        except voice_exceptions.DomainActionError as e:
            status_code = getattr(e, "status_code", None)

            # Preserve previous soft‑failure semantics for MQTT publish errors:
            # return HTTP 200 along with the current lamp state and message.
            if status_code == 200:
                serializer = LampViewSerializer(
                    Lamp.objects.get(pk=lamp.pk),
                    context=self.get_serializer_context(),
                )
                return Response(
                    {
                        "detail": str(e),
                        "lamp": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

            # For permission errors (403) and timeouts (504), bubble up the
            # original status code so clients see the same behaviour as before.
            return Response(
                {"detail": str(e)},
                status=status_code or status.HTTP_400_BAD_REQUEST,
            )

        # On success, return the full lamp representation as before.
        serializer = LampViewSerializer(
            Lamp.objects.get(pk=lamp.pk),
            context=self.get_serializer_context(),
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

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
    
