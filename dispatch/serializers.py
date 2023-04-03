# from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import DispatchOrderWaypoint, DispatchOrder, DispatchRegularly, DispatchRegularlyConnect, DispatchOrderConnect

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

    class Meta:
        model = DispatchRegularlyConnect
        fields = ['detailed_route', 'group', 'references', 'departure', 'arrival', 'week', 'route', 'departure_date', 'arrival_date', 'bus_id', 'price', 'driver_allowance']

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
    class Meta:
        model = DispatchOrderConnect
        fields = ['order_id', 'references', 'departure', 'arrival', 'departure_date', 'arrival_date', 'bus_id', 'price', 'driver_allowance']
        # fields = ['order_id', 'departure_date', 'arrival_date', 'bus_id', 'price', 'driver_allowance']
        

# 노선명(출발지/도착지) ㅇ
# 사람 
# 차량 ㅇ
# 금액 ㅇ
# 기사수당 ㅇ
# 운행요일(날짜)ㅇ
# 그룹ㅇ
# 운행시간 출발 도착 ㅇ
# 참조사항 ㅇ
# 상세노선 ㅇ
