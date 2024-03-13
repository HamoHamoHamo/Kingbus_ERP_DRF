from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password

from .models import Member, AccidentCase

class UserLoginSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=128, write_only=True)
    
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    def validate(self, data):
        # if data['user_id'].isdigit():
        #     try:user = Member.objects.get(num=data['user_id'])
        #     finally:pass
        # elif '@' in data['user_id']:
        #     try:user = Member.objects.get(email=data['user_id'])
        #     finally:pass
        # else:

        try:
            user = Member.objects.get(user_id=data['user_id'])
        # user = authenticate(**data)
        # if user is None:
        except:
            raise serializers.ValidationError("Invalid ID")
        # if data['role'] is None:
        #     raise serializers.ValidationError("Invalid login credentials2")
        # if len(data['role'])>1:
        #     raise serializers.ValidationError("Bad Request")
        if not check_password(data['password'], user.password):
            raise serializers.ValidationError("Invalid password")
        if user.role == '임시' or user.use == '삭제' or user.use == '미사용':
            raise serializers.ValidationError("Invalid user")
        # if data['role']!=user.role:
        #     raise serializers.ValidationError("Invalid login credentials")
        # TODO https://eunjin3786.tistory.com/271
    
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
        # refresh['name'] = user.name
        access_token = str(refresh.access_token)
        

        # update_last_login(None, user)
        validation = {
            'access': access_token,
            'refresh': refresh_token,
            'user_id': user.user_id,
            'name': user.name,
            'role' : user.role
        }
        return validation

class MemberListSerializer(serializers.ModelSerializer):
	class Meta:
		model = Member
		fields = ['name', 'role', 'phone_num']

class MemberSerializer(serializers.ModelSerializer):
	class Meta:
		model = Member
		fields = ['id', 'user_id', 'name', 'role', 'phone_num', 'base', 'service_allowance', 'annual_allowance', 'performance_allowance', 'meal']
            
class AccidentCaseSereializer(serializers.ModelSerializer):
    class Meta:
        model = AccidentCase
        fields = ['member','date','creator','carnum','route_name','accident_description', 'picture_our_vehicle', 'picture_thier_vehicle', 'picture_all_vehicles', 'picture_from_far', 'picture_from_close', 'picture_passenger_list']
        # 'kind_of_accident','damaged_car','accident_location','accident_time_occur','accident_time_solve','vehicle_speed','passenger_count',

