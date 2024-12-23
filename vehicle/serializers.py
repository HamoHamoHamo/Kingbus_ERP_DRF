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

class RefuelingListSerializer(serializers.ModelSerializer) :
    vehicle_num = serializers.CharField(source = 'vehicle.vehicle_num') # vehicle 차량 번호
    driver_name = serializers.CharField(source = 'driver.name') # 기사 이름
    gas_station_name = serializers.CharField(source = 'gas_station.category') # 주유소 이름

    class Meta:
         model = Refueling
         fields = ['refueling_date', 'driver_name', 'vehicle_num', 'km', 'refueling_amount', 'urea_solution', 'gas_station_name']