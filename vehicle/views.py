from django.core import serializers
from django.shortcuts import get_object_or_404
from django.http import Http404, JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Vehicle
from humanresource.models import Member

class VehicleListView(APIView):
    def get(self, request):
        response = {}
        response['driver_vehicle_list'] = Vehicle.objects.filter(use='사용').filter(driver_id=request.user.id).values('id', 'vehicle_num0', 'vehicle_num')
        response['vehicle_list'] = Vehicle.objects.filter(use='사용').exclude(driver_id=request.user.id).values('id', 'vehicle_num0', 'vehicle_num')
        return Response(response, status=status.HTTP_200_OK)
       