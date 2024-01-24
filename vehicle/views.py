from datetime import datetime
from django.core import serializers
from django.shortcuts import get_object_or_404
from django.http import Http404, JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from trp_drf.settings import DATE_FORMAT

from .serializers import RefuelingSerializer, DailyChecklistSerializer, WeeklyChecklistSerializer, EquipmentChecklistSerializer
from .models import Vehicle, DailyChecklist, WeeklyChecklist, EquipmentChecklist
from crudmember.models import Category
from humanresource.models import Member


class VehicleListView(APIView):
    def get(self, request):
        response = {}
        response['driver_vehicle_list'] = Vehicle.objects.filter(use='사용').filter(driver_id=request.user.id).values('id', 'vehicle_num0', 'vehicle_num')
        response['vehicle_list'] = Vehicle.objects.filter(use='사용').exclude(driver_id=request.user.id).values('id', 'vehicle_num0', 'vehicle_num')
        return Response(response, status=status.HTTP_200_OK)
       
class RefuelingView(APIView):
    def post(self, request):
        try:
            datetime.strptime(request.data['refueling_date'], "%Y-%m-%d %H:%M")
        except ValueError:
            response = {
                'result' : 'false',
                'data' : 1,
                'message' : {
                    'error' : 'Invalid format',
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        data = {
            'refueling_date' : request.data['refueling_date'],
            'vehicle' : request.data['vehicle'],
            'driver' : request.data['driver'],
            'km' : request.data['km'],
            'refueling_amount' : request.data['refueling_amount'],
            'urea_solution' : request.data['urea_solution'],
            'gas_station' : request.data['gas_station'],
            'creator' : request.user.id,
        }
        serializer = RefuelingSerializer(data=data)
        if serializer.is_valid(raise_exception=False):
            serializer.save()
            response = {
                'result' : 'true',
                'data' : serializer.data,
                'message' : ''
            }
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            response = {
                'result': 'false',
                'data': '2',
                'message': serializer.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

class DailyChecklistView(APIView):
    def get(self, request, date):
        try:
            datetime.strptime(date, DATE_FORMAT)
        except Exception as e:
            response = {
                'result': 'false',
                'data': '1',
                'message': {
                    'error' : 'invalid date format'
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checklist = DailyChecklist.objects.filter(date=date).get(member=request.user)    
        except DailyChecklist.DoesNotExist:
            checklist = DailyChecklist(
                date = date,
                member = request.user,
                creator = request.user
            )
            checklist.save()
            
        data = DailyChecklistSerializer(checklist).data
        response = {
            'result': 'true',
            'data': data,
            'message': ''
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, date):
        data = request.data.copy()
        data['member'] = request.user.id
        data['creator'] = request.user.id
        data['date'] = date

        try:
            datetime.strptime(date, DATE_FORMAT)
        except Exception as e:
            response = {
                'result': 'false',
                'data': '1',
                'message': {
                    'error' : 'invalid date format'
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checklist = DailyChecklist.objects.filter(date=date).get(member=request.user)    
            serializer = DailyChecklistSerializer(checklist, data=data)
        except DailyChecklist.DoesNotExist:
            serializer = DailyChecklistSerializer(data=data)
        
        if serializer.is_valid():
            instance = serializer.save()
            instance.submit_check = True
            instance.save()
            response = {
                'result': 'true',
                'data': serializer.data,
                'message': ''
            }
            return Response(response, status=status.HTTP_200_OK)
        response = {
            'result': 'false',
            'data': '2',
            'message': {
                'error': serializer.errors
            }
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

class WeeklyChecklistView(APIView):
    def get(self, request, date):
        try:
            datetime.strptime(date, DATE_FORMAT)
        except Exception as e:
            response = {
                'result': 'false',
                'data': '1',
                'message': {
                    'error' : 'invalid date format'
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checklist = WeeklyChecklist.objects.filter(date=date).get(member=request.user)    
        except WeeklyChecklist.DoesNotExist:
            checklist = WeeklyChecklist(
                date = date,
                member = request.user,
                creator = request.user
            )
            checklist.save()
            
        data = WeeklyChecklistSerializer(checklist).data
        response = {
            'result': 'true',
            'data': data,
            'message': ''
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, date):
        data = request.data.copy()
        data['member'] = request.user.id
        data['creator'] = request.user.id
        data['date'] = date

        try:
            datetime.strptime(date, DATE_FORMAT)
        except Exception as e:
            response = {
                'result': 'false',
                'data': '1',
                'message': {
                    'error' : 'invalid date format'
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checklist = WeeklyChecklist.objects.filter(date=date).get(member=request.user)    
            serializer = WeeklyChecklistSerializer(checklist, data=data)
        except WeeklyChecklist.DoesNotExist:
            serializer = WeeklyChecklistSerializer(data=data)
        
        if serializer.is_valid():
            instance = serializer.save()
            instance.submit_check = True
            instance.save()
            response = {
                'result': 'true',
                'data': serializer.data,
                'message': ''
            }
            return Response(response, status=status.HTTP_200_OK)
        response = {
            'result': 'false',
            'data': '2',
            'message': {
                'error': serializer.errors
            }
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

class EquipmentChecklistView(APIView):
    def get(self, request, date):
        try:
            datetime.strptime(date, DATE_FORMAT)
        except Exception as e:
            response = {
                'result': 'false',
                'data': '1',
                'message': {
                    'error' : 'invalid date format'
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checklist = EquipmentChecklist.objects.filter(date=date).get(member=request.user)    
        except EquipmentChecklist.DoesNotExist:
            checklist = EquipmentChecklist(
                date = date,
                member = request.user,
                creator = request.user
            )
            checklist.save()
            
        data = EquipmentChecklistSerializer(checklist).data
        response = {
            'result': 'true',
            'data': data,
            'message': ''
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, date):
        data = request.data.copy()
        data['member'] = request.user.id
        data['creator'] = request.user.id
        data['date'] = date

        try:
            datetime.strptime(date, DATE_FORMAT)
        except Exception as e:
            response = {
                'result': 'false',
                'data': '1',
                'message': {
                    'error' : 'invalid date format'
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checklist = EquipmentChecklist.objects.filter(date=date).get(member=request.user)    
            serializer = EquipmentChecklistSerializer(checklist, data=data)
        except EquipmentChecklist.DoesNotExist:
            serializer = EquipmentChecklistSerializer(data=data)
        
        if serializer.is_valid():
            instance = serializer.save()
            instance.submit_check = True
            instance.save()
            response = {
                'result': 'true',
                'data': serializer.data,
                'message': ''
            }
            return Response(response, status=status.HTTP_200_OK)
        response = {
            'result': 'false',
            'data': '2',
            'message': {
                'error': serializer.errors
            }
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
