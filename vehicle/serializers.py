from rest_framework import serializers

from .models import Refueling


class RefuelingSerializer(serializers.ModelSerializer):
	class Meta:
		model = Refueling
		fields = '__all__'
