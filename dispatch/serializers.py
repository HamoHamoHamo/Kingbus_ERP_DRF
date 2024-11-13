# from django.contrib.auth import authenticate
from datetime import datetime, timedelta
from rest_framework import serializers
from django.shortcuts import get_object_or_404

from common.validators import TimeFormatValidator, DateFormatValidator
from .models import DispatchOrderStation, DispatchOrder, DispatchRegularly, \
    DispatchRegularlyConnect, DispatchOrderConnect, DriverCheck, ConnectRefusal, \
    DispatchRegularlyWaypoint, DispatchRegularlyRouteKnow, DispatchRegularlyData, \
    RegularlyGroup, MorningChecklist, EveningChecklist, DrivingHistory, DispatchOrderTourCustomer, ConnectStatusFieldMapping, StationArrivalTime
from crudmember.models import Category
from humanresource.models import Member

WORK_TYPE_CHOICES = ['출근', '퇴근', '일반']

class CheckTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverCheck
        fields = ['wake_time', 'drive_time', 'departure_time', 'connect_check']

class DispatchRegularlyWaypointSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchRegularlyWaypoint
        fields = ['waypoint']

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
    price = serializers.ReadOnlyField(source="regularly_id.price")
    driver_allowance = serializers.ReadOnlyField(source="regularly_id.driver_allowance")
    week = serializers.ReadOnlyField(source="regularly_id.week")
    work_type = serializers.ReadOnlyField(source="regularly_id.work_type")
    route = serializers.ReadOnlyField(source="regularly_id.route")
    location = serializers.ReadOnlyField(source="regularly_id.location")
    detailed_route = serializers.ReadOnlyField(source="regularly_id.detailed_route")
    maplink = serializers.ReadOnlyField(source="regularly_id.maplink")
    bus_id = serializers.ReadOnlyField(source="bus_id.vehicle_num")
    check_regularly_connect = CheckTimeSerializer(read_only=True)
    waypoint = DispatchRegularlyWaypointSerializer(many=True, source="regularly_id.regularly_id.regularly_waypoint")

    class Meta:
        model = DispatchRegularlyConnect
        fields = ['id', 'price', 'driver_allowance', 'work_type', 'route', 'location', 'check_regularly_connect', 'detailed_route', 'maplink', 'group', 'references', 'departure', 'arrival', 'week', 'route', 'departure_date', 'arrival_date', 'bus_id', 'price', 'driver_allowance', 'waypoint']

class DispatchOrderStationSerializer(serializers.ModelSerializer):
    waypoint = serializers.SerializerMethodField()

    class Meta:
        model = DispatchOrderStation
        fields = ['station_name', 'time', 'delegate', 'delegate_phone', 'waypoint']

    def get_waypoint(self, obj):
        return obj.station_name


class DispatchOrderSerializer(serializers.ModelSerializer):
    waypoint = DispatchOrderStationSerializer(many=True)


    class Meta:
        model = DispatchOrder
        # fields = ['references', 'route']
        fields = ['waypoint']

class DispatchOrderConnectSerializer(serializers.ModelSerializer):
    waypoint = DispatchOrderStationSerializer(many=True, source="order_id.station")
    # waypoint = serializers.ReadOnlyField(source="order_id__waypoint")
    operation_type = serializers.ReadOnlyField(source="order_id.operation_type")
    bus_type = serializers.ReadOnlyField(source="order_id.bus_type")
    bus_cnt = serializers.ReadOnlyField(source="order_id.bus_cnt")
    price = serializers.ReadOnlyField(source="order_id.price")
    driver_allowance = serializers.ReadOnlyField(source="order_id.driver_allowance")
    cost_type = serializers.ReadOnlyField(source="order_id.cost_type")
    customer = serializers.ReadOnlyField(source="order_id.customer")
    customer_phone = serializers.ReadOnlyField(source="order_id.customer_phone")
    collection_type = serializers.ReadOnlyField(source="order_id.collection_type")
    payment_method = serializers.ReadOnlyField(source="order_id.payment_method")
    VAT = serializers.ReadOnlyField(source="order_id.VAT")
    option = serializers.ReadOnlyField(source="order_id.option")
    ticketing_info = serializers.ReadOnlyField(source="order_id.ticketing_info")
    order_type = serializers.ReadOnlyField(source="order_id.order_type")
    
    departure = serializers.ReadOnlyField(source="order_id.departure")
    arrival = serializers.ReadOnlyField(source="order_id.arrival")
    references = serializers.ReadOnlyField(source="order_id.references")
    bus_id = serializers.ReadOnlyField(source="bus_id.vehicle_num")
    check_order_connect = CheckTimeSerializer(read_only=True) # model에 있는 필드 이름이랑 같아야 되는듯?
    class Meta:
        model = DispatchOrderConnect
        fields = ['id', 
        'operation_type',
        'bus_type',
        'bus_cnt',
        'price',
        'driver_allowance',
        'cost_type',
        'customer',
        'customer_phone',
        'collection_type',
        'payment_method',
        'VAT',
        'option',
        'ticketing_info',
        'order_type',
        'waypoint', 
        'check_order_connect', 
        'references', 
        'departure', 
        'arrival', 
        'departure_date', 
        'arrival_date', 
        'bus_id',
        'price', 
        'driver_allowance'
        ]
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
            raise serializers.ValidationError("Invalid time format")
        # 종류3개중 어느것도 아닐때
        if check_type != '기상' and check_type != '운행' and check_type != '출발지': 
            raise serializers.ValidationError("Invalid Type")
        if not attrs['regularly_id'] and not attrs['order_id']:
            raise serializers.ValidationError("No regularly_id and order_id")
        
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

class DriverCheckRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    work_type = serializers.ChoiceField(choices=WORK_TYPE_CHOICES)
    time = serializers.CharField(validators=[TimeFormatValidator()])
    type = serializers.ChoiceField(choices=[key.value for key in ConnectStatusFieldMapping.DRIVER_CHECK_STATUS_FIELD_MAP])

class StationArrivalTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StationArrivalTime
        exclude = ['creator']


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

class RegularlyKnowSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchRegularlyRouteKnow
        fields = '__all__'


class DispatchRegularlyDataSerializer(serializers.ModelSerializer):
    know = serializers.SerializerMethodField()

    class Meta:
        model = DispatchRegularlyData
        fields = '__all__'

    def get_know(self, obj):
        user_id = self.context.get('user_id')
        if obj.regularly_route_know.filter(driver_id=user_id).exists():
            return 'true'
        else:
            return 'false'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['group'] = RegularlyGroup.objects.get(id=representation['group']).name if representation['group'] else None

        return representation

class DispatchRegularlyGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegularlyGroup
        fields = ['id', 'name']

class MorningChecklistSerializer(serializers.ModelSerializer):
    bus = serializers.SerializerMethodField()
    
    class Meta:
        model = MorningChecklist
        fields = [
            'member',
            'date',
            'arrival_time',
            'garage_location',
            'health_condition',
            'cleanliness_condition',
            'route_familiarity',
            'alcohol_test',
            'bus',
            'creator',
            'submit_check',
        ]
    
    def get_bus(self, obj):
        return obj.get_vehicle_list()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['member'] = Member.objects.get(id=representation['member']).name if representation['member'] else None

        return representation

class EveningChecklistSerializer(serializers.ModelSerializer):
    bus = serializers.SerializerMethodField()

    class Meta:
        model = EveningChecklist
        fields = [
            'member',
            'date',
            'garage_location',
            'battery_condition',
            'drive_distance',
            'fuel_quantity',
            'urea_solution_quantity',
            'suit_gauge',
            'special_notes',
            'bus',
            'creator',
            'submit_check',
            'checklist_submit_time',
            'tomorrow_check_submit_time',
            'get_off_submit_time',
        ]

    def get_bus(self, obj):
        return obj.get_vehicle()
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['member'] = Member.objects.get(id=representation['member']).name if representation['member'] else None
        representation['garage_location'] = Category.objects.get(id=representation['garage_location']).category if representation['garage_location'] else None

        return representation

class DrivingHistorySerializer(serializers.ModelSerializer):
    connect = serializers.SerializerMethodField()

    class Meta:
        model = DrivingHistory
        fields = [
            'date',
            'member',
            'regularly_connect_id',
            'order_connect_id',
            'departure_km',
            'arrival_km',
            'passenger_num',
            'special_notes',
            'departure_date',
            'arrival_date',
            'creator',
            'connect',
            'submit_check',
        ]
    def validate(self, attrs):
        super().validate(attrs)
        if 'departure_date' in attrs:
            try:
                datetime.strptime(attrs['departure_date'], "%Y-%m-%d %H:%M")
            except:
                raise serializers.ValidationError("invalid date format")
        if 'arrival_date' in attrs:
            try:
                datetime.strptime(attrs['arrival_date'], "%Y-%m-%d %H:%M")
            except:
                raise serializers.ValidationError("invalid date format")
        return attrs
    
    def get_connect(self, obj):
        return obj.get_connect_data()
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['member'] = Member.objects.get(id=representation['member']).name if representation['member'] else None
        return representation

class ConnectRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    work_type = serializers.ChoiceField(choices=WORK_TYPE_CHOICES)


class TeamRegularlyConnectSerializer(serializers.ModelSerializer):
    departure_time = serializers.SerializerMethodField()
    problem = serializers.SerializerMethodField()
    route = serializers.CharField(source='regularly_id.route', read_only=True)
    departure = serializers.CharField(source='regularly_id.departure', read_only=True)
    references = serializers.CharField(source='regularly_id.references', read_only=True)
    vehicle_num = serializers.CharField(source='bus_id.vehicle_num', read_only=True)

    class Meta:
        model = DispatchRegularlyConnect
        fields = [
            'route',
            'vehicle_num',
            'departure',
            'departure_time',
            'references',
            'problem',
        ]


    def get_departure_time(self, obj):
        return obj.departure_date[11:16]

    def get_problem(self, obj):
        driver_check = obj.check_regularly_connect
        departure_time = self.get_departure_time(obj)

        temp_time = datetime.strptime(departure_time, "%H:%M")
        check_time1 = datetime.strftime(temp_time - timedelta(hours=1.5), "%H:%M")
        check_time2 = datetime.strftime(temp_time - timedelta(hours=1), "%H:%M")
        check_time3 = datetime.strftime(temp_time - timedelta(minutes=20), "%H:%M")
        current_time = datetime.strftime(datetime.now(), "%H:%M")

        problem = ''
        if current_time > check_time1 and not driver_check.wake_time:
            problem = '기상 문제 발생'
        if current_time > check_time2 and not driver_check.drive_time:
            problem = '운행시작 문제 발생'
        if current_time > check_time3 and not driver_check.departure_time:
            problem = '첫 정류장 문제 발생'

        return problem

class TeamOrderConnectSerializer(serializers.ModelSerializer):
    departure_time = serializers.SerializerMethodField()
    problem = serializers.SerializerMethodField()
    route = serializers.CharField(source='order_id.route', read_only=True)
    departure = serializers.CharField(source='order_id.departure', read_only=True)
    references = serializers.CharField(source='order_id.references', read_only=True)
    vehicle_num = serializers.CharField(source='bus_id.vehicle_num', read_only=True)

    class Meta:
        model = DispatchRegularlyConnect
        fields = [
            'route',
            'vehicle_num',
            'departure',
            'departure_time',
            'references',
            'problem',
        ]


    def get_departure_time(self, obj):
        return obj.departure_date[11:16]

    def get_problem(self, obj):
        driver_check = obj.check_order_connect
        departure_time = self.get_departure_time(obj)

        temp_time = datetime.strptime(departure_time, "%H:%M")
        check_time1 = datetime.strftime(temp_time - timedelta(hours=1.5), "%H:%M")
        check_time2 = datetime.strftime(temp_time - timedelta(hours=1), "%H:%M")
        check_time3 = datetime.strftime(temp_time - timedelta(minutes=20), "%H:%M")
        current_time = datetime.strftime(datetime.now(), "%H:%M")

        problem = ''
        if current_time > check_time1 and not driver_check.wake_time:
            problem = '기상 문제 발생'
        if current_time > check_time2 and not driver_check.drive_time:
            problem = '운행시작 문제 발생'
        if current_time > check_time3 and not driver_check.departure_time:
            problem = '첫 정류장 문제 발생'

        return problem

class DispatchOrderEstimateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchOrder
        fields = '__all__'

class DispatchOrderStationEstimateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchOrderStation
        fields = '__all__'

class DispatchOrderTourCustomerSerializer(serializers.ModelSerializer):
    tour_uid = serializers.CharField(source='tour_id.firebase_uid', read_only=True)

    class Meta:
        model = DispatchOrderTourCustomer
        fields = '__all__'

class LocationHistoryRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()

class LocationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchRegularlyConnect
        fields = ['id', 'locations']
        read_only_fields = ['id']

# 하루일과 배차데이터
class DailyDispatchRegularlyConnectListSerializer(serializers.ModelSerializer):
    dispatch_id = serializers.IntegerField(source='id')
    departure = serializers.CharField(source='regularly_id.departure')
    arrival = serializers.CharField(source='regularly_id.arrival')
    bus_num = serializers.CharField(source='bus_id.vehicle_num')
    status_info = serializers.SerializerMethodField()
    
    class Meta:
        model = DispatchRegularlyConnect
        fields = [
            'dispatch_id',
            'work_type',
            'bus_id',
            'bus_num',
            'departure',
            'departure_date',
            'arrival',
            'arrival_date',
            'status',
            'status_info',
        ]

    def get_status_info(self, obj):
        try:
            driver_check = DriverCheck.objects.get(regularly_id=obj)
        except DriverCheck.DoesNotExist:
            return []

        status_info = []
        # 운행 준비, 탑승 및 운행 시작, 첫 정류장 도착, 운행 출발, 운행 종료 시간 데이터 리스트로 만들기
        for status, field_name in ConnectStatusFieldMapping.DRIVER_CHECK_STATUS_FIELD_MAP.items():
            completion_time = getattr(driver_check, field_name, "")
            status_info.append({
                "status_name": status.value,
                "completion_time": completion_time
            })
        return status_info

# 하루일과 배차데이터
class DailyDispatchOrderConnectListSerializer(serializers.ModelSerializer):
    dispatch_id = serializers.IntegerField(source='id')
    departure = serializers.CharField(source='order_id.departure')
    arrival = serializers.CharField(source='order_id.arrival')
    bus_num = serializers.CharField(source='bus_id.vehicle_num')
    status_info = serializers.CharField(default="", allow_blank=True)
    
    class Meta:
        model = DispatchOrderConnect
        fields = [
            'dispatch_id',
            'work_type',
            'bus_num',
            'departure',
            'departure_date',
            'arrival',
            'arrival_date',
            'status',
            'status_info',
        ]

# 퇴근 데이터
class GetOffWorkDataSerialzier(serializers.ModelSerializer):
    roll_call_time = serializers.CharField(source='checklist_submit_time')
    tomorrow_dispatch_check_time = serializers.CharField(source='tomorrow_check_submit_time')
    get_off_time = serializers.CharField(source='get_off_submit_time')
    

    class Meta:
        model = EveningChecklist
        fields = [
            'roll_call_time',
            'tomorrow_dispatch_check_time',
            'get_off_time',
        ]

class GetOffWorkRequestSerializer(serializers.Serializer):
    date = serializers.CharField(validators=[DateFormatValidator()])
    status_type = serializers.ChoiceField(choices=EveningChecklist.STATUS_TYPE_CHOCIES)