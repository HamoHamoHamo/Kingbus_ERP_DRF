from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from .models import Client

class ClientListSerializer(serializers.ModelSerializer):
	class Meta:
		model = Client
		fields = ['name', 'phone']