from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.shortcuts import get_object_or_404
from django.http import Http404, JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from trp_drf.settings import DATE_FORMAT ,TODAY
from .models import Consulting, VehicleInspectionRequest, InspectionRequestFile, ConsultingFile
from .serializers import ConsultingSerializer, VehicleInspectionRequestSerializer
from humanresource.models import Member
from vehicle.models import Vehicle

class ConsultingView(APIView):
    def get(self, request):
        consulting_list = Consulting.objects.filter(member_id=request.user.id).order_by('-pub_date')
        response = ConsultingSerializer(consulting_list, many=True).data
        return Response(response, status=status.HTTP_200_OK)
    def post(self, request):
        files = request.FILES.getlist('files')
        data = {
            'member_id' : request.user.id,
            'content' : request.data['content'],
            'creator' : request.user.id,
            'date' : str(datetime.now())[:16]
        }
        serializer = ConsultingSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            consulting = serializer.save()
            try:
                consulting_file_save(files, consulting)
                response = {
                    'data' : serializer.data,
                    'success': True,
                }
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": f'{e}', "message": "File Save Error."}, status=status.HTTP_409_CONFLICT)
        else:
            return Response({"message": "Request Body Error."}, status=status.HTTP_409_CONFLICT)

def consulting_file_save(upload_files, consulting):
    for file in upload_files:
        consulting_file = ConsultingFile(
            consulting_id=consulting,
            file=file,
            filename=file.name,
        )
        consulting_file.save()
    return

class InspectionView(APIView):
    def get(self, request):
        inspection_list = VehicleInspectionRequest.objects.filter(member_id=request.user.id).select_related('vehicle_id', 'check_member_id').order_by('-pub_date')
        response = VehicleInspectionRequestSerializer(inspection_list, many=True).data
        return Response(response, status=status.HTTP_200_OK)
    def post(self, request):
        files = request.FILES.getlist('files')
        data = {
            'member_id' : request.user.id,
            'vehicle_id' : request.data['vehicle_id'],
            'content' : request.data['content'],
            'creator' : request.user.id,
            'date' : str(datetime.now())[:16]
        }
        serializer = VehicleInspectionRequestSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            inspection = serializer.save()
            try:
                inspection_file_save(files, inspection)
                response = {
                    'data' : serializer.data,
                    'success': True,
                }
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": f'{e}', "message": "File Save Error."}, status=status.HTTP_409_CONFLICT)    
        else:
            return Response({"message": "Request Body Error."}, status=status.HTTP_409_CONFLICT)

def inspection_file_save(upload_files, inspection):
    for file in upload_files:
        inspection_file = InspectionRequestFile(
            inspection_request_id=inspection,
            file=file,
            filename=file.name,
        )
        inspection_file.save()
    return