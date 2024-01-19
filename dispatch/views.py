from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import Http404, JsonResponse

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


from trp_drf.settings import DATE_FORMAT ,TODAY
from trp_drf.pagination import Pagination
from humanresource.models import Member
from .models import DriverCheck, DispatchRegularlyData, RegularlyGroup, DispatchOrderConnect, DispatchRegularlyConnect, ConnectRefusal, DispatchRegularlyRouteKnow, MorningChecklist, EveningChecklist, DrivingHistory, DailyChecklist, WeeklyChecklist, EquipmentChecklist
from .serializers import DispatchRegularlyConnectSerializer, DispatchOrderConnectSerializer, \
    DriverCheckSerializer, ConnectRefusalSerializer, RegularlyKnowSerializer, DrivingHistorySerializer, \
    DispatchRegularlyDataSerializer, DispatchRegularlyGroupSerializer, MorningChecklistSerializer, EveningChecklistSerializer, \
    DailyChecklistSerializer, WeeklyChecklistSerializer, EquipmentChecklistSerializer, TeamRegularlyConnectSerializer, TeamOrderConnectSerializer

def get_invalid_date_format_response():
    response = {
        'result': 'false',
        'data': '1',
        'message': {
            'error' : 'invalid date format'
        },
    }
    return response

class MonthlyDispatches(APIView):
    def get(self, request, month):
        try:
            last_day = datetime.strftime(datetime.strptime(f'{month}-01', DATE_FORMAT) + relativedelta(months=1) - timedelta(days=1), DATE_FORMAT)[8:]
        except ValueError:
            return Response(get_invalid_date_format_response(), status=status.HTTP_400_BAD_REQUEST)
        user = request.user

        order = [0] * int(last_day)
        regularly_c = [0] * int(last_day)
        regularly_t = [0] * int(last_day)

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
        response = {
            'result' : 'true',
            'data' : {
                'order' : order,
                'regularly_c' : regularly_c,
                'regularly_t' : regularly_t,
            },
            'message' : '',
        }
        return Response(response, status=status.HTTP_200_OK)

class DailyDispatches(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, date):
        try:
            datetime.strptime(date, DATE_FORMAT)
        except ValueError:
            return Response(get_invalid_date_format_response(), status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        r_connects = DispatchRegularlyConnect.objects.prefetch_related('check_regularly_connect').select_related('regularly_id').filter(departure_date__startswith=date).filter(driver_id=user)
        connects = DispatchOrderConnect.objects.prefetch_related('check_order_connect').select_related('order_id').filter(departure_date__startswith=date).filter(driver_id=user)
        res = {}
        res['regularly'] = DispatchRegularlyConnectSerializer(r_connects, many=True).data
        res['order'] = DispatchOrderConnectSerializer(connects, many=True).data
        response = {
            'result' : 'true',
            'data' : res,
            'message' : '',
        }
        return Response(response, status=status.HTTP_200_OK)

class DriverCheckView(APIView):
    def patch(self, request):
        regularly_id = request.data['regularly_id']
        order_id = request.data['order_id']

        e_response = {
            'result': 'false',
        }
        if ((not regularly_id and not order_id) or regularly_id and order_id):
            e_response['data'] = '1'
            e_response['message'] = {'connect': 'regularly_id, order_id 둘 중에 하나만 입력해주세요'}
            return Response(e_response, status=status.HTTP_400_BAD_REQUEST)
        
        if regularly_id:
            try:
                connect = DispatchRegularlyConnect.objects.get(id=regularly_id)
            except DispatchRegularlyConnect.DoesNotExist:
                e_response['data'] = '2'
                e_response['message'] = {'regularly_id': 'Invalid regulalry_id'}
                return Response(e_response, status=status.HTTP_400_BAD_REQUEST)
            try:
                driver_check = DriverCheck.objects.get(regularly_id=connect)
            except DriverCheck.DoesNotExist:
                e_response['data'] = '2'
                e_response['message'] = {'driver_check': 'DriverCheck does not exist'}
                return Response(e_response, status=status.HTTP_400_BAD_REQUEST)
        elif order_id:
            try:
                connect = DispatchOrderConnect.objects.get(id=order_id)
            except DispatchOrderConnect.DoesNotExist:
                e_response['data'] = '2'
                e_response['message'] = {'order_id': 'Invalid order_id'}
                return Response(e_response, status=status.HTTP_400_BAD_REQUEST)
            try:
                driver_check = DriverCheck.objects.get(order_id=connect)
            except DriverCheck.DoesNotExist:
                e_response['data'] = '2'
                e_response['message'] = {'driver_check': 'DriverCheck does not exist'}
                return Response(e_response, status=status.HTTP_400_BAD_REQUEST)
        
        if connect.driver_id != request.user:
            e_response['data'] = '3'
            e_response['message'] = {'user': 'Invalid user'}
            return Response(e_response, status=status.HTTP_401_UNAUTHORIZED)

        serializer = DriverCheckSerializer(driver_check, data=request.data, context={
            'time' : request.data['time'],
            'check_type' : request.data['check_type'],
        })
        if serializer.is_valid(raise_exception=False):
            serializer.save()
            response = {
                'result': 'true',
                'data': serializer.data,
                'message': '',
            }
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            e_response['data'] = '1'
            e_response['message'] = serializer.errors
            return Response(e_response, status=status.HTTP_400_BAD_REQUEST)

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
    
class RegularlyList(ListAPIView):
    serializer_class = DispatchRegularlyDataSerializer
    pagination_class = Pagination

    def get_queryset(self):
        group_id = self.request.GET.get('group', '')
        search = self.request.GET.get('search', '')

        if not group_id:
            group = RegularlyGroup.objects.order_by('number').first()
            return DispatchRegularlyData.objects.filter(group=group).filter(Q(route__contains=search) | Q(departure__contains=search) | Q(arrival__contains=search)).filter(use='사용').order_by('num1', 'number1', 'num2', 'number2')
        else:
            group = get_object_or_404(RegularlyGroup, id=group_id)
            return DispatchRegularlyData.objects.filter(group=group).filter(Q(route__contains=search) | Q(departure__contains=search) | Q(arrival__contains=search)).filter(use='사용').order_by('num1', 'number1', 'num2', 'number2')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_id'] = self.request.user.id
        return context

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        data = {
            'result': 'true',
            'data': {
                'count': response.data['count'],
                'next': response.data['next'],
                'previous': response.data['previous'],
                'regularly_list': response.data['results'],
            },
            'message': '',
        }
        return Response(data)

    def handle_exception(self, exc):
        return Response({
            'result': 'false',
            'data' : 1,
            'message': {
                'detail': str(exc),
            },
        }, status=400)

class RegularlyGroupList(ListAPIView):
    queryset = RegularlyGroup.objects.all().order_by('number')
    serializer_class = DispatchRegularlyGroupSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        data = {
            'result': 'true',
            'data': {
                'group_list': response.data['results'],
            },
            'message': '',
        }
        return Response(data)

    def handle_exception(self, exc):
        return Response({
                'result': 'false',
                'data' : 1,
                'message': {
                    'detail': str(exc),
                },
            }, status=400)

class RegularlyKnow(APIView):
    def post(self, request):
        data = request.data.copy()
        data['regularly_id'] = request.data['regularly_id']
        if 'driver_id' in request.data:
            data['driver_id'] = request.data['driver_id']
        else:
            data['driver_id'] = request.user.id
        data['creator'] = request.user.id

        if DispatchRegularlyRouteKnow.objects.filter(driver_id=data['driver_id']).filter(regularly_id=data['regularly_id']).exists():
            response = {
                'result': 'false',
                'data': 2,
                'message': {
                    'detail': '이미 생성한 노선숙지입니다'
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        serializer = RegularlyKnowSerializer(data=data)
        if serializer.is_valid(raise_exception=False):
            serializer.save()
            response = {
                'result': 'true',
                'data': serializer.data,
                'message': '',
            }
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            response = {
                'result': 'false',
                'data': '1',
                'message': serializer.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request):
        data = {
            'regularly_id' : request.data['regularly_id'],
            'driver_id' : request.data['driver_id'] if 'driver_id' in request.data else request.user.id
        }
        
        serializer = RegularlyKnowSerializer(data=data)
        if not serializer.is_valid(raise_exception=False):
            response = {
                'result': 'false',
                'data': '1',
                'message': serializer.errors
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        route_know = DispatchRegularlyRouteKnow.objects.filter(regularly_id=data['regularly_id']).filter(driver_id=data['driver_id'])
        if route_know:
            route_know.delete()
            response = {
                'result': 'true',
                'data': route_know,
                'message': '',
            }
            return Response(response, status=status.HTTP_200_OK)
        else:
            response = {
                'result': 'false',
                'data': '1',
                'message': {
                    'regularly_id': '노선숙지가 없습니다'
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
class MorningChecklistView(APIView):
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
            checklist = MorningChecklist.objects.filter(date=date).get(member=request.user)    
        except MorningChecklist.DoesNotExist:
            checklist = MorningChecklist(
                date = date,
                member = request.user,
                creator = request.user
            )
            checklist.save()
            
        data = MorningChecklistSerializer(checklist).data
        response = {
            'result': 'true',
            'data': data,
            'message': ''
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, date):
        data = request.data.copy()
        data['member'] = request.user.id
        data['date'] = date
        data['creator'] = request.user.id

        try:
            datetime.strptime(date, DATE_FORMAT)
            datetime.strptime(request.data['arrival_time'], "%H:%M")
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
            checklist = MorningChecklist.objects.filter(date=date).get(member=request.user)    
            serializer = MorningChecklistSerializer(checklist, data=data)
        except MorningChecklist.DoesNotExist:
            serializer = MorningChecklistSerializer(data=data)
        
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

class EveningChecklistView(APIView):
    def get(self, request, date):
        try:
            datetime.strptime(date, DATE_FORMAT)
        except Exception as e:
            return Response(get_invalid_date_format_response(), status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checklist = EveningChecklist.objects.filter(date=date).get(member=request.user)    
        except EveningChecklist.DoesNotExist:
            checklist = EveningChecklist(
                date = date,
                member = request.user,
                creator = request.user
            )
            checklist.save()
            
        data = EveningChecklistSerializer(checklist).data
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
            return Response(get_invalid_date_format_response(), status=status.HTTP_400_BAD_REQUEST)
        
        try:
            checklist = EveningChecklist.objects.filter(date=date).get(member=request.user)    
            serializer = EveningChecklistSerializer(checklist, data=data)
        except EveningChecklist.DoesNotExist:
            serializer = EveningChecklistSerializer(data=data)
        
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

class DrivingHistoryView(APIView):
    def return_invalid_connect_id_response(self, data_num):
        response = {
                'result': 'false',
                'data': data_num,
                'message': {
                    'error' : 'invalid connect id'
                },
            }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        regularly_connect_id = self.request.GET.get('regularly_connect_id')
        order_connect_id = self.request.GET.get('order_connect_id')

        if regularly_connect_id and order_connect_id:
            return self.return_invalid_connect_id_response('1')
        try:
            if regularly_connect_id:
                connect = DispatchRegularlyConnect.objects.filter(driver_id=request.user).get(id=regularly_connect_id)
                driving_history = DrivingHistory.objects.get(regularly_connect_id=regularly_connect_id)
            elif order_connect_id:
                connect = DispatchOrderConnect.objects.filter(driver_id=request.user).get(id=order_connect_id)
                driving_history = DrivingHistory.objects.get(order_connect_id=order_connect_id)
            else:
                return self.return_invalid_connect_id_response('1')
        except DrivingHistory.DoesNotExist:
            driving_history = DrivingHistory(
                member = request.user,
                creator = request.user,
            )
            if regularly_connect_id:
                driving_history.regularly_connect_id = connect
            elif order_connect_id:
                driving_history.order_connect_id = connect
            driving_history.date = connect.departure_date[:10]
            driving_history.save()
        except DispatchOrderConnect.DoesNotExist:
            return self.return_invalid_connect_id_response('1')
        except DispatchRegularlyConnect.DoesNotExist:
            return self.return_invalid_connect_id_response('1')

        data = DrivingHistorySerializer(driving_history).data
        response = {
            'result': 'true',
            'data': data,
            'message': ''
        }
        return Response(response, status=status.HTTP_200_OK)

    def patch(self, request):
        data = request.data.copy()
        data['member'] = request.user.id
        data['creator'] = request.user.id

        if data['regularly_connect_id'] and data['order_connect_id']:
            return self.return_invalid_connect_id_response('1')

        try:
            if data['regularly_connect_id']:
                connect = DispatchRegularlyConnect.objects.filter(driver_id=request.user).get(id=data['regularly_connect_id'])
                driving_history = DrivingHistory.objects.get(regularly_connect_id=connect)
            elif data['order_connect_id']:
                connect = DispatchOrderConnect.objects.filter(driver_id=request.user).get(id=data['order_connect_id'])
                driving_history = DrivingHistory.objects.get(order_connect_id=connect)
            else:
                return self.return_invalid_connect_id_response('1')
            date = connect.departure_date[:10]
        except Exception as e:
            return self.return_invalid_connect_id_response('1')

        serializer = DrivingHistorySerializer(driving_history, data=data)
        
        if serializer.is_valid():
            instance = serializer.save()
            instance.submit_check = True
            instance.date = date
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

class TeamConnectListView(APIView):
    def get(self, request):
        user = request.user
        if user.authority > 3:
            response = {
                'result': 'false',
                'data': '1',
                'message': {
                'error': 'authority_error'
                }
            }
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

        team = user.team
        if team:
            member_list = team.member_team.all().order_by('name')
        else:
            member_list = ''
        data_list = []
        for member in member_list:
            regularly_connect_list = DispatchRegularlyConnect.objects.filter(driver_id=member).filter(departure_date__startswith=TODAY).order_by('departure_date')
            order_connect_list = DispatchOrderConnect.objects.filter(driver_id=member).filter(departure_date__startswith=TODAY).order_by('departure_date')
            current_time = str(datetime.now())[:16]

            current_regularly_connect = regularly_connect_list.filter(departure_date__gte=current_time).first()
            if not current_regularly_connect:
                current_regularly_connect = regularly_connect_list.last()
            current_order_connect = order_connect_list.filter(departure_date__gte=current_time).first()
            if not current_order_connect:
                current_order_connect = order_connect_list.last()
            total_count = regularly_connect_list.count() + order_connect_list.count()
            current_count = regularly_connect_list.filter(departure_date__lte=current_time).count() + order_connect_list.filter(departure_date__lte=current_time).count() + 1
            if current_count > total_count:
                current_count = total_count

            if not current_order_connect and not current_regularly_connect:
                data = {
                    'member' : member.name,
                    'member_id' : member.id,
                    'current_count' : 0,
                    'total_count' : 0,
                    'bus' : '',
                    'route' : '',
                    'departure_time' : '',
                    'check1' : '',
                    'check2' : '',
                    'check3' : '',
                }
                data_list.append(data)
                continue
            elif (not current_order_connect and current_regularly_connect) or \
                (current_order_connect and current_regularly_connect and \
                current_regularly_connect.departure_date < current_order_connect.departure_date):
                bus = current_regularly_connect.bus_id.vehicle_num
                departure_time = current_regularly_connect.departure_date[11:16]
                route = current_regularly_connect.regularly_id.route
                driver_check = current_regularly_connect.check_regularly_connect

            else:
                bus = current_order_connect.bus_id.vehicle_num
                departure_time = current_order_connect.departure_date[11:16]
                route = current_order_connect.order_id.route
                driver_check = current_order_connect.check_order_connect

            temp_time = datetime.strptime(departure_time, "%H:%M")
            check_time1 = datetime.strftime(temp_time - timedelta(hours=1.5), "%H:%M")
            check_time2 = datetime.strftime(temp_time - timedelta(hours=1), "%H:%M")
            check_time3 = datetime.strftime(temp_time - timedelta(minutes=20), "%H:%M")
            current_time = datetime.strftime(datetime.now(), "%H:%M")

            check1 = 'true'
            check2 = 'true'
            check3 = 'true'
            if current_time > check_time1 and not driver_check.wake_time:
                check1 = 'false'
            if current_time > check_time2 and not driver_check.drive_time:
                check2 = 'false'
            if current_time > check_time3 and not driver_check.departure_time:
                check3 = 'false'

            data = {
                'member' : member.name,
                'member_id' : member.id,
                'current_count' : current_count,
                'total_count' : total_count,
                'bus' : bus,
                'route' : route,
                'departure_time' : departure_time,
                'check1' : check1,
                'check2' : check2,
                'check3' : check3,
            }
            data_list.append(data)

        response = {
            'result': 'true',
            'data': data_list,
            'message': ''
        }
        return Response(response, status=status.HTTP_200_OK)

class TeamDriverConnectView(APIView):
    def get(self, request, id):
        user = request.user
        if user.authority > 3:
            response = {
                'result': 'false',
                'data': '1',
                'message': {
                    'error': 'authority_error'
                }
            }
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

        member = get_object_or_404(Member, id=id)
        morning_checklist = MorningChecklist.objects.filter(date=TODAY)
        if morning_checklist:
            alcohol_test = morning_checklist[0].alcohol_test
        else:
            alcohol_test = ''
        
        regularly_connect_list = DispatchRegularlyConnect.objects.filter(driver_id=member).filter(departure_date__startswith=TODAY).order_by('departure_date')
        order_connect_list = DispatchOrderConnect.objects.filter(driver_id=member).filter(departure_date__startswith=TODAY).order_by('departure_date')

        regularly_data = TeamRegularlyConnectSerializer(regularly_connect_list, many=True).data
        order_data = TeamOrderConnectSerializer(order_connect_list, many=True).data

        data = {
            'phone' : member.phone_num,
            'alcohol_test' : alcohol_test,
            'regularly' : regularly_data,
            'order' : order_data,
            #'test' : regularly_data + order_data,
        }

        response = {
            'result': 'true',
            'data': data,
            'message': ''
        }
        return Response(response, status=status.HTTP_200_OK)


    
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