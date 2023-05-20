# from django.contrib.auth import authenticate
from datetime import datetime
from rest_framework import serializers
from django.shortcuts import get_object_or_404

from .models import DispatchOrderWaypoint, DispatchOrder, DispatchRegularly, DispatchRegularlyConnect, DispatchOrderConnect, DriverCheck, ConnectRefusal

class CheckTimeSerializer(serializers.ModelSerializer):
	class Meta:
		model = DriverCheck
		fields = ['wake_time', 'drive_time', 'departure_time', 'connect_check']

class DispatchRegularlySerializer(serializers.ModelSerializer):
	group = serializers.ReadOnlyField(source="group.name")
	# connect = DispatchRegularlyConnectSerializer(many=True)

	class Meta:
		model = DispatchRegularly
		fields = ['group', 'departure', 'price', 'driver_allowance',  'departure_time', 'arrival', 'arrival_time', 'work_type', 'route']

class DispatchRegularlyConnectSerializer(serializers.ModelSerializer):
	# regularly_id = DispatchRegularlySerializer()
	route = serializers.ReadOnlyField(source="regularly_id.route")
	group = serializers.ReadOnlyField(source="regularly_id.group.name")
	references = serializers.ReadOnlyField(source="regularly_id.references")
	departure = serializers.ReadOnlyField(source="regularly_id.departure")
	arrival = serializers.ReadOnlyField(source="regularly_id.arrival")
	week = serializers.ReadOnlyField(source="regularly_id.week")
	detailed_route = serializers.ReadOnlyField(source="regularly_id.detailed_route")
	bus_id = serializers.ReadOnlyField(source="bus_id.vehicle_num")
	check_regularly_connect = CheckTimeSerializer(read_only=True)

	class Meta:
		model = DispatchRegularlyConnect
		fields = ['id', 'check_regularly_connect', 'detailed_route', 'group', 'references', 'departure', 'arrival', 'week', 'route', 'departure_date', 'arrival_date', 'bus_id', 'price', 'driver_allowance']

class DispatchOrderWaypointSerializer(serializers.ModelSerializer):
	class Meta:
		model = DispatchOrderWaypoint
		fields = ['waypoint', 'time', 'delegate', 'delegate_phone']

class DispatchOrderSerializer(serializers.ModelSerializer):
	waypoint = DispatchOrderWaypointSerializer(many=True)


	class Meta:
		model = DispatchOrder
		# fields = ['references', 'route']
		fields = ['waypoint']

class DispatchOrderConnectSerializer(serializers.ModelSerializer):
	order_id = DispatchOrderSerializer(many=False)
	# waypoint = serializers.ReadOnlyField(source="order_id__waypoint")
	departure = serializers.ReadOnlyField(source="order_id.departure")
	arrival = serializers.ReadOnlyField(source="order_id.arrival")
	references = serializers.ReadOnlyField(source="order_id.references")
	bus_id = serializers.ReadOnlyField(source="bus_id.vehicle_num")
	check_order_connect = CheckTimeSerializer(read_only=True) # model에 있는 필드 이름이랑 같아야 되는듯?
	class Meta:
		model = DispatchOrderConnect
		fields = ['id', 'order_id', 'check_order_connect', 'references', 'departure', 'arrival', 'departure_date', 'arrival_date', 'bus_id', 'price', 'driver_allowance']
		# fields = ['order_id', 'departure_date', 'arrival_date', 'bus_id', 'price', 'driver_allowance']
		
class DriverCheckSerializer(serializers.ModelSerializer):
	class Meta:
		model = DriverCheck
		fields = '__all__'

	def validate(self, attrs):
		time = self.context['time']
		check_type = self.context['check_type']
		try:
			datetime.strptime(time, "%H:%M")
		except ValueError:
			raise serializers.ValidationError("Time Format Error")
		# 종류3개중 어느것도 아닐때
		if check_type != '기상' and check_type != '운행' and check_type != '출발지': 
			raise serializers.ValidationError("Bad Request. Type Error")
		if not attrs['regularly_id'] and not attrs['order_id']:
			raise serializers.ValidationError("Bad Request. Connect Error")
		
		return attrs

	def update(self, instance, validated_data):
		check_type = self.context['check_type']
		time = self.context['time']

		if check_type == '기상':
			instance.wake_time = time
		elif check_type == '운행':
			instance.drive_time = time
		elif check_type == '출발지':
			instance.departure_time = time
		instance.save()
		return instance

class ConnectRefusalSerializer(serializers.ModelSerializer):
	class Meta:
		model = ConnectRefusal
		fields = '__all__'

	#def create(self, request, *args, **kwargs):
	#	check_type = self.context['check_type']
	#	time = self.context['time']

	#	if check_type == '기상':
	#		instance.wake_time = time
	#	elif check_type == '운행':
	#		instance.drive_time = time
	#	elif check_type == '출발지':
	#		instance.departure_time = time
	#	instance.save()
	#	return instance