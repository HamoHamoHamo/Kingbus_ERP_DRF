from datetime import datetime
from rest_framework import serializers
from django.shortcuts import get_object_or_404

from .models import Consulting, VehicleInspectionRequest, InspectionRequestFile
from vehicle.models import Vehicle
from humanresource.models import Member

class ConsultingSerializer(serializers.ModelSerializer):
    #check_member_id = serializers.ReadOnlyField(source="check_member_id.name")
    
    # field = '__all__'로 쓰면 def get_(field명) 함수가 실행이 안됨
    #def get_check_member_id(self, obj):
    #    if obj.check_member_id:
    #        return obj.check_member_id.name
    #    else:
    #        return None
        
    class Meta:
        model = Consulting
        #fields = ['id', 'content', 'date', 'status', 'check_member_id']
        fields = '__all__'
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['check_member_id'] = Member.objects.get(id=representation['check_member_id']).name if representation['check_member_id'] else None
        del representation['creator']
        del representation['member_id']
        del representation['pub_date']
        del representation['updated_at']
        return representation

class InspectionRequestFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionRequestFile
        fields = ['file', 'filename']

class VehicleInspectionRequestSerializer(serializers.ModelSerializer):
    inspection_request_file = InspectionRequestFileSerializer(many=True, required=False)
    #check_member_id_name = serializers.ReadOnlyField(source="check_member_id.name")
    #vehicle_id_vehicle_num = serializers.ReadOnlyField(source="vehicle_id.vehicle_num")

    #check_member_id = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all(), required=False)
    #vehicle_id = serializers.PrimaryKeyRelatedField(queryset=Vehicle.objects.all())

    #def get_check_member_id(self, obj):
    #    if obj.check_member_id:
    #        return obj.check_member_id.name
    #    else:
    #        return None
    #def get_vehicle_id(self, obj):
    #    return obj.vehicle_id.vehicle_num

    class Meta:
        model = VehicleInspectionRequest
        #fields = ['id', 'content', 'date', 'status', 'vehicle_id', 'check_member_id', 'inspection_request_file']
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['check_member_id'] = Member.objects.get(id=representation['check_member_id']).name if representation['check_member_id'] else None
        representation['vehicle_id'] = Vehicle.objects.get(id=representation['vehicle_id']).vehicle_num if representation['vehicle_id'] else None
        del representation['creator']
        del representation['member_id']
        del representation['pub_date']
        del representation['updated_at']
        return representation
    