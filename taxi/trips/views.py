from django.shortcuts import render
from django.db.models import Q

# Create your views here.
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, viewsets
from .serializers import UserSerializer, LogInSerializer, TripSerializer, NestedTripSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Trip


class SignUpView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class LogInView(TokenObtainPairView):
    serializer_class = LogInSerializer


class TripView(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'id'
    lookup_url_kwarg = 'trip_id'
    permission_classes = (permissions.IsAuthenticated, )
    queryset = Trip.objects.all()
    serializer_class = NestedTripSerializer

    def get_queryset(self):
        # Retrieve the user model in the request
        user = self.request.user
        if user.group == 'driver':
            # Return all Trip objects associated with that driver of which are REQUESTED
            # Or has the user as the driver
            return Trip.objects.filter(
                Q(status=Trip.REQUESTED) | Q(driver=user)
            )
        if user.group == 'rider':
            # Return all of the Trip objects associated with that user
            return Trip.objects.filter(rider=user)
        return Trip.objects.none()
