from rest_framework import serializers

from .models import Refueling, DailyChecklist, WeeklyChecklist, EquipmentChecklist


class RefuelingSerializer(serializers.ModelSerializer):
	class Meta:
		model = Refueling
		fields = '__all__'

class DailyChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyChecklist
        fields = "__all__"


class WeeklyChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyChecklist
        fields = "__all__"


class EquipmentChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentChecklist
        fields = "__all__"