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
from .models import DriverCheck, DispatchRegularly, DispatchOrder, DispatchOrderConnect, DispatchRegularlyConnect, ConnectRefusal
from .serializers import DispatchRegularlyConnectSerializer, DispatchOrderConnectSerializer, DriverCheckSerializer, ConnectRefusalSerializer
from humanresource.models import Member

class MonthlyDispatches(APIView):
	def get(self, request, month):
		if not month or len(month) != 7:
			return Response("날짜를 정확하게 입력하세요", status=status.HTTP_400_BAD_REQUEST)
		user = request.user

		last_day = datetime.strftime(datetime.strptime(f'{month}-01', DATE_FORMAT) + relativedelta(months=1) - timedelta(days=1), DATE_FORMAT)[8:]
		order = [0] * int(last_day)
		regularly_c = [0] * int(last_day)
		regularly_t = [0] * int(last_day)
		response = {}

		regularly_list = DispatchRegularlyConnect.objects.filter(departure_date__startswith=month).filter(driver_id=user)
		order_list = DispatchOrderConnect.objects.filter(departure_date__startswith=month).filter(driver_id=user)

		for regularly in regularly_list:
			date = int(regularly.departure_date[8:10])
			if (regularly.work_type == '출근'):
				regularly_c[date-1] += 1
			elif (regularly.work_type == '퇴근'):
				regularly_t[date-1] += 1
		
		for o in order_list:
			date = int(o.departure_date[8:10])
			order[date-1] += 1
		response['order'] = order
		response['regularly_c'] = regularly_c
		response['regularly_t'] = regularly_t
		return Response(response, status=status.HTTP_200_OK)

class DailyDispatches(APIView):
	permission_classes = (IsAuthenticated,)
	def get(self, request, date):
		if not date or len(date) != 10:
			return Response("날짜를 정확하게 입력하세요", status=status.HTTP_400_BAD_REQUEST)

		user = request.user
		r_connects = DispatchRegularlyConnect.objects.prefetch_related('check_regularly_connect').select_related('regularly_id').filter(departure_date__startswith=date).filter(driver_id=user)
		connects = DispatchOrderConnect.objects.prefetch_related('check_order_connect').select_related('order_id').filter(departure_date__startswith=date).filter(driver_id=user)
		res = {}
		res['regularly'] = DispatchRegularlyConnectSerializer(r_connects, many=True).data
		res['order'] = DispatchOrderConnectSerializer(connects, many=True).data
		return Response(res, status=status.HTTP_200_OK)

class DriverCheckView(APIView):
	def patch(self, request):
		regularly_id = request.data['regularly_id']
		order_id = request.data['order_id']

		if ((not regularly_id and not order_id) or regularly_id and order_id):
			return Response("Connect Error", status=status.HTTP_400_BAD_REQUEST)
		
		if regularly_id:
			connect_type = "regularly"
			connect = get_object_or_404(DispatchRegularlyConnect, id=regularly_id)
			try:
				driver_check = DriverCheck.objects.get(regularly_id=connect)
			except DriverCheck.DoesNotExist:
				return Response("No DriverCheck Error", status=status.HTTP_400_BAD_REQUEST)
		elif order_id:
			connect_type = "order"
			connect = get_object_or_404(DispatchOrderConnect, id=order_id)
			try:
				driver_check = DriverCheck.objects.get(order_id=connect)
			except DriverCheck.DoesNotExist:
				return Response("No DriverCheck", status=status.HTTP_400_BAD_REQUEST)
		
		if not connect or connect.driver_id != request.user:
			return Response("Connect Error", status=status.HTTP_400_BAD_REQUEST)

		serializer = DriverCheckSerializer(driver_check, data=request.data, context={
			'time' : request.data['time'],
			'check_type' : request.data['check_type'],
		})
		if serializer.is_valid(raise_exception=True):
			serializer.save()
			response = {
				'success': True,
				'statusCode': status.HTTP_201_CREATED,
			}
			return Response(response, status=status.HTTP_201_CREATED)
		else:
			return Response({"message": "Request Body Error."}, status=status.HTTP_409_CONFLICT)

class ConnectCheckView(APIView):
	def post(self, request):
		regularly_id = request.data['regularly_id']
		order_id = request.data['order_id']

		if ((not regularly_id and not order_id) or regularly_id and order_id):
			return Response("Connect Error", status=status.HTTP_400_BAD_REQUEST)
		
		if regularly_id:
			connect = get_object_or_404(DispatchRegularlyConnect, id=regularly_id)
			route = connect.regularly_id.route
			try:
				driver_check = DriverCheck.objects.get(regularly_id=connect)
			except DriverCheck.DoesNotExist:
				return Response("No DriverCheck Error", status=status.HTTP_400_BAD_REQUEST)
		elif order_id:
			connect = get_object_or_404(DispatchOrderConnect, id=order_id)
			route = connect.order_id.route
			try:
				driver_check = DriverCheck.objects.get(order_id=connect)
			except DriverCheck.DoesNotExist:
				return Response("No DriverCheck", status=status.HTTP_400_BAD_REQUEST)
		
		if not connect or connect.driver_id != request.user:
			return Response("Connect Error", status=status.HTTP_400_BAD_REQUEST)

		if driver_check.connect_check != '':
			return Response("Already check Error", status=status.HTTP_400_BAD_REQUEST)
		
		# 배차 수락하면 return 200
		if request.data['check'] == '1':
			driver_check.connect_check = 1
			driver_check.save()
			return Response({'success': True}, status=status.HTTP_200_OK)

		data = request.data.copy()
		data['driver_id'] = request.user.id
		data['departure_date'] = connect.departure_date
		data['arrival_date'] = connect.arrival_date
		data['check_date'] = TODAY
		data['creator'] = request.user.id
		data['route'] = route
		
		serializer = ConnectRefusalSerializer(data=data)
		if serializer.is_valid(raise_exception=True):
			driver_check.connect_check = 0
			driver_check.save()
			serializer.save()
			response = {
				'data' : serializer.data,
				'success': True,
			}
			return Response(response, status=status.HTTP_201_CREATED)
		else:
			return Response({"message": "Request Body Error."}, status=status.HTTP_409_CONFLICT)

	
class ResetConnectCheck(APIView):
	def post(self, request):
		regularly_id = request.data['regularly_id']
		order_id = request.data['order_id']

		if ((not regularly_id and not order_id) or regularly_id and order_id):
			return Response("Connect Error", status=status.HTTP_400_BAD_REQUEST)
		
		if regularly_id:
			connect = get_object_or_404(DispatchRegularlyConnect, id=regularly_id)
			try:
				driver_check = DriverCheck.objects.get(regularly_id=connect)
			except DriverCheck.DoesNotExist:
				return Response("No DriverCheck Error", status=status.HTTP_400_BAD_REQUEST)
			connect_refusal = ConnectRefusal.objects.filter(regularly_id=connect)
			
		elif order_id:
			connect = get_object_or_404(DispatchOrderConnect, id=order_id)
			try:
				driver_check = DriverCheck.objects.get(order_id=connect)
			except DriverCheck.DoesNotExist:
				return Response("No DriverCheck", status=status.HTTP_400_BAD_REQUEST)
			connect_refusal = ConnectRefusal.objects.filter(order_id=connect)
		
		if not connect or connect.driver_id != request.user:
			return Response("Connect Error", status=status.HTTP_400_BAD_REQUEST)

		# 확인 끝
		driver_check.connect_check = ''
		driver_check.save()
		response = {
			'success': True,
			'delete connect_refusal' : connect_refusal.count(),
		}
		if connect_refusal:
			connect_refusal.delete()

		return Response(response, status=status.HTTP_200_OK)