# from django.contrib.auth import authenticate
from datetime import datetime, timedelta
from rest_framework import serializers
from django.shortcuts import get_object_or_404

from common.validators import TimeFormatValidator, DateFormatValidator
from .models import DispatchOrderStation, DispatchOrder, DispatchRegularly, \
    DispatchRegularlyConnect, DispatchOrderConnect, DriverCheck, ConnectRefusal, \
    DispatchRegularlyWaypoint, DispatchRegularlyRouteKnow, DispatchRegularlyData, \
    RegularlyGroup, MorningChecklist, EveningChecklist, DrivingHistory, DispatchOrderTourCustomer, \
        ConnectStatusFieldMapping, StationArrivalTime, DispatchRegularlyStation, DispatchRegularlyFavorite
from crudmember.models import Category
from vehicle.models import DailyChecklist
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

# 정기배차리스트
class DispatchRegularlyConnectListSerializer(serializers.ModelSerializer):
    work_type = serializers.ReadOnlyField(source="regularly_id.work_type")
    bus_num = serializers.ReadOnlyField(source="bus_id.vehicle_num")
    arrival = serializers.ReadOnlyField(source="regularly_id.arrival")
    maplink = serializers.ReadOnlyField(source="regularly_id.maplink")
    departure = serializers.ReadOnlyField(source="regularly_id.departure")
    connect_check = serializers.SerializerMethodField() 
    is_vehicle_checked = serializers.SerializerMethodField() 
    status = serializers.ReadOnlyField()

    class Meta:
        model = DispatchRegularlyConnect
        fields = ['id', 'work_type', 'bus_id', 'bus_num' ,'departure_date', 'arrival_date', 'departure', 'arrival', 'maplink', 'connect_check', 'is_vehicle_checked', 'status']
    
    def get_connect_check(self, obj):
        # connect_check 값을 "1" 또는 "0"으로 저장한 경우 "true"/"false"로 변환
        check_value = obj.check_regularly_connect.connect_check if obj.check_regularly_connect else ""
        if check_value == "1":
            return "true"
        elif check_value == "0":
            return "false"
        # 수락이나 거절 안 했을 떄 ""
        else:
            return ""
    
    def get_is_vehicle_checked(self, obj):
        # departure_date에서 날짜 부분만 추출
        try:
            formatted_date = datetime.strptime(obj.departure_date[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return "false"  # 형식이 맞지 않는 경우 기본값 반환

        # 정확히 날짜와 버스 ID가 일치하는 DailyChecklist 조회
        checklist = DailyChecklist.objects.filter(bus_id=obj.bus_id, date=formatted_date).first()
        return "true" if checklist and checklist.submit_check else "false"

# 정기배차 정류장
class DispatchRegularlyStationSerializer(serializers.ModelSerializer):
    station_name = serializers.ReadOnlyField(source="station.name")  # 정류장 이름
    station_type = serializers.ReadOnlyField()  # 정류장 종류
    latitude = serializers.ReadOnlyField(source="station.latitude")  # 위도
    longitude = serializers.ReadOnlyField(source="station.longitude")  # 경도
    target_time = serializers.ReadOnlyField(source="time")  # DispatchRegularlyDataStation의 time을 target_time으로 사용
    arrival_time = serializers.SerializerMethodField()  # 도착 시간을 SerializerMethodField로 변경

    class Meta:
        model = DispatchRegularlyStation  # DispatchRegularlyStation에서 정보를 가져옴
        fields = ['id', 'station_name', 'station_type', 'latitude', 'longitude', 'target_time', 'arrival_time']

    def get_arrival_time(self, obj):
        # 해당 정류장에 연결된 StationArrivalTime 가져오기
        arrival_time_entry = obj.station_arrival_time.last()  # station_arrival_time은 related_name
        return arrival_time_entry.arrival_time if arrival_time_entry else ""

# 정기배차상세
class DispatchRegularlyConnectDetailSerializer(serializers.ModelSerializer):
    stations = serializers.SerializerMethodField()  # 필터링된 정류장 목록 가져오기
    bus_num = serializers.ReadOnlyField(source="bus_id.vehicle_num")  # 버스 번호
    references = serializers.ReadOnlyField(source="regularly_id.references")  # DispatchRegularly 모델의 references 필드
    maplink = serializers.ReadOnlyField(source="regularly_id.maplink")
    class Meta:
        model = DispatchRegularlyConnect  # 정기 배차 모델
        fields = ['id', 'work_type', 'bus_id', 'bus_num', 'stations', 'references', 'locations', 'maplink']
    
    def get_stations(self, obj):
        # obj의 work_type에 따라 정류장을 필터링
        work_type = obj.work_type  # DispatchRegularlyConnect 인스턴스의 work_type

        if work_type == '출근':
            filtered_stations = obj.regularly_id.regularly_station.filter(station_type__in=['정류장', '사업장'])
        elif work_type == '퇴근':
            filtered_stations = obj.regularly_id.regularly_station.filter(station_type__in=['사업장', '정류장', '마지막 정류장'])
        else:
            filtered_stations = obj.regularly_id.regularly_station.all()  # 기본값은 전체 정류장

        return DispatchRegularlyStationSerializer(filtered_stations, many=True).data

# 문제 정기배차리스트
class ProblemRegularlyConnectListSerializer(serializers.ModelSerializer):
    work_type = serializers.ReadOnlyField(source="regularly_id.work_type")
    bus_num = serializers.ReadOnlyField(source="bus_id.vehicle_num")
    arrival = serializers.ReadOnlyField(source="regularly_id.arrival")
    departure = serializers.ReadOnlyField(source="regularly_id.departure")
    route = serializers.ReadOnlyField(source="regularly_id.route")
    group = serializers.ReadOnlyField(source="regularly_id.group.name")

    class Meta:
        model = DispatchRegularlyConnect
        fields = ['id', 'work_type', 'bus_num' ,'departure_date', 'arrival_date', 'departure', 'arrival', 'route', 'group']

# 문제 정기배차 정류장
class ProblemRegularlyStationSerializer(serializers.ModelSerializer):
    station_name = serializers.ReadOnlyField(source="station.name")  # 정류장 이름
    station_type = serializers.ReadOnlyField()  # 정류장 종류
    latitude = serializers.ReadOnlyField(source="station.latitude")  # 위도
    longitude = serializers.ReadOnlyField(source="station.longitude")  # 경도
    target_time = serializers.ReadOnlyField(source="time")  # DispatchRegularlyDataStation의 time을 target_time으로 사용
    arrival_time = serializers.SerializerMethodField()  # 도착 시간을 SerializerMethodField로 변경

    class Meta:
        model = DispatchRegularlyStation  # DispatchRegularlyStation에서 정보를 가져옴
        fields = ['id', 'station_name', 'station_type', 'latitude', 'longitude', 'target_time', 'arrival_time']

    def get_arrival_time(self, obj):
        # 해당 정류장에 연결된 StationArrivalTime 가져오기
        arrival_time_entry = obj.station_arrival_time.first()  # station_arrival_time은 related_name
        return arrival_time_entry.arrival_time if arrival_time_entry else ""       

# 문제 정기배차상세
class ProblemRegularlyConnectDetailSerializer(serializers.ModelSerializer):
    driver_name = serializers.ReadOnlyField(source="driver_id.name")  # 기사 이름
    driver_phone = serializers.ReadOnlyField(source="driver_id.phone_num")  # 기사 전화번호
    bus_num = serializers.ReadOnlyField(source="bus_id.vehicle_num")  # 버스 번호
    group = serializers.ReadOnlyField(source="regularly_id.group.name")  # 그룹명
    route = serializers.ReadOnlyField(source="regularly_id.route")  # 노선명
    departure = serializers.ReadOnlyField(source="regularly_id.departure")  # 출발지
    arrival = serializers.ReadOnlyField(source="regularly_id.arrival")  # 도착지
    problem = serializers.ReadOnlyField(source="status")  # 문제 상태
    stations = serializers.SerializerMethodField()  # 정류장 리스트

    class Meta:
        model = DispatchRegularlyConnect  # 정기 배차 모델
        fields = [
            'driver_name', 'driver_phone', 'bus_num', 'group', 'route',
            'departure', 'arrival', 'departure_date', 'arrival_date',
            'problem', 'stations'
        ]
    
    def get_stations(self, obj):
        # obj의 work_type에 따라 정류장을 필터링
        work_type = obj.work_type  # DispatchRegularlyConnect 인스턴스의 work_type

        if work_type == '출근':
            filtered_stations = obj.regularly_id.regularly_station.filter(station_type__in=['정류장', '사업장'])
        elif work_type == '퇴근':
            filtered_stations = obj.regularly_id.regularly_station.filter(station_type__in=['사업장', '정류장', '마지막 정류장'])
        else:
            filtered_stations = obj.regularly_id.regularly_station.all()  # 기본값은 전체 정류장

        return DispatchRegularlyStationSerializer(filtered_stations, many=True).data
    
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

# 일반배차리스트
class DispatchOrderConnectListSerializer(serializers.ModelSerializer):
    arrival = serializers.ReadOnlyField(source="order_id.arrival")
    bus_num = serializers.ReadOnlyField(source="bus_id.vehicle_num")
    departure = serializers.ReadOnlyField(source="order_id.departure")
    work_type = serializers.ReadOnlyField()
    maplink = serializers.SerializerMethodField()
    connect_check = serializers.SerializerMethodField()
    is_vehicle_checked = serializers.SerializerMethodField()  
    status = serializers.ReadOnlyField()


    class Meta:
        model = DispatchOrderConnect
        fields = ['id', 'work_type', 'bus_id', 'bus_num','departure_date', 'arrival_date', 'departure', 'arrival', 'maplink', 'connect_check', 'is_vehicle_checked', 'status']
    
    def get_maplink(self, obj):
        # 일반 배차에는 maplink가 없으므로 빈 문자열을 반환
        return ""
    
    def get_connect_check(self, obj):
        # connect_check 값을 "1" 또는 "0"으로 저장한 경우 "true"/"false"로 변환
        check_value = obj.check_order_connect.connect_check if obj.check_order_connect else "0"
        return "true" if check_value == "1" else "false"    

    def get_is_vehicle_checked(self, obj):
        # departure_date에서 날짜 부분만 추출
        try:
            formatted_date = datetime.strptime(obj.departure_date[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return "false"  # 형식이 맞지 않는 경우 기본값 반환

        # 정확히 날짜와 버스 ID가 일치하는 DailyChecklist 조회
        checklist = DailyChecklist.objects.filter(bus_id=obj.bus_id, date=formatted_date).first()
        return "true" if checklist and checklist.submit_check else "false"
    
# 일반배차상세
class DispatchOrderConnectDetailSerializer(serializers.ModelSerializer):
    stations = serializers.SerializerMethodField()  # 항상 null 반환
    bus_num = serializers.ReadOnlyField(source="bus_id.vehicle_num")  # 버스 번호
    references = serializers.ReadOnlyField(source="order_id.references")  # DispatchOrder 모델의 references 필드
    locations = serializers.SerializerMethodField()  # 항상 null 반환

    class Meta:
        model = DispatchOrderConnect
        fields = ['id', 'work_type', 'bus_id', 'bus_num', 'stations', 'references', 'locations']

    def get_stations(self, obj):
        # 일반 배차의 경우 stations는 빈 리스트로 반환
        return None
    
    def get_locations(self, obj):
        # 일반 배차의 경우 stations는 빈 리스트로 반환
        return None

# 문제 일반배차리스트
class ProblemOrderConnectListSerializer(serializers.ModelSerializer):
    arrival = serializers.ReadOnlyField(source="order_id.arrival")
    bus_num = serializers.ReadOnlyField(source="bus_id.vehicle_num")
    departure = serializers.ReadOnlyField(source="order_id.departure")
    work_type = serializers.ReadOnlyField()
    route = serializers.ReadOnlyField(source="order_id.route")
    group = serializers.SerializerMethodField()

    class Meta:
        model = DispatchOrderConnect
        fields = ['id', 'work_type', 'bus_num','departure_date', 'arrival_date', 'departure', 'arrival', 'route', 'group']

    def get_group(self, obj):
        # 일반 배차에는 group이 없으므로 빈 문자열을 반환
        return ""   

# 문제 일반배차상세 
class ProblemOrderConnectDetailSerializer(serializers.ModelSerializer):
    driver_name = serializers.ReadOnlyField(source="driver_id.name")  # 기사 이름
    driver_phone = serializers.ReadOnlyField(source="driver_id.phone_num")  # 기사 전화번호
    bus_num = serializers.ReadOnlyField(source="bus_id.vehicle_num")  # 버스 번호
    route = serializers.ReadOnlyField(source="order_id.route")  # 노선명
    departure = serializers.ReadOnlyField(source="order_id.departure")  # 출발지
    arrival = serializers.ReadOnlyField(source="order_id.arrival")  # 도착지
    problem = serializers.ReadOnlyField(source="status")  # 문제 상태
    stations = serializers.SerializerMethodField()  # 정류장 리스트
    group = serializers.SerializerMethodField()

    class Meta:
        model = DispatchOrderConnect
        fields = [
            'driver_name', 'driver_phone', 'bus_num', 'route', 'departure',
            'arrival', 'departure_date', 'arrival_date', 'problem', 'stations', 'group'
        ]

    def get_stations(self, obj):
        # 일반 배차에서는 정류장 리스트를 빈 리스트로 반환
        return None
    
    def get_group(self, obj):
        # 일반 배차에는 group이 없으므로 빈 문자열을 반환
        return ""   
    
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

# 배차 즐겨찾기
class DispatchRegularlyFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchRegularlyFavorite
        fields = '__all__'

class DispatchRegularlyDataSerializer(serializers.ModelSerializer):
    know = serializers.SerializerMethodField()

    class Meta:
        model = DispatchRegularlyData
        fields = '__all__'

    def get_know(self, obj):
        # 미리 annotate된 값을 사용
        return obj.is_known if hasattr(obj, 'is_known') else 'false'

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
