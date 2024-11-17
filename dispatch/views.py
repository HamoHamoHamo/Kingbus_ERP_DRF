import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404, render
from django.http import Http404, JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.constant import DATE_TIME_FORMAT
from common.response import set_response_false, set_response_true, StandardResponse
from trp_drf.settings import DATE_FORMAT, TODAY, BASE_DIR
from firebase.firebase_file import upload_files
from trp_drf.pagination import Pagination
from humanresource.models import Member
from .models import DriverCheck, DispatchRegularlyData, RegularlyGroup, DispatchOrderConnect, DispatchRegularlyConnect, ConnectRefusal, DispatchRegularlyRouteKnow, MorningChecklist, EveningChecklist, DrivingHistory, DispatchOrder, DispatchOrderStation, DispatchOrderTour, DispatchOrderTourCustomer, ConnectStatusFieldMapping, ConnectStatus, StationArrivalTime
from .services import DispatchConnectService
from .serializers import DispatchRegularlyConnectSerializer, DispatchOrderConnectSerializer, \
    DriverCheckSerializer, ConnectRefusalSerializer, RegularlyKnowSerializer, DrivingHistorySerializer, \
    DispatchRegularlyDataSerializer, DispatchRegularlyGroupSerializer, MorningChecklistSerializer, EveningChecklistSerializer, \
    TeamRegularlyConnectSerializer, TeamOrderConnectSerializer, DispatchOrderEstimateSerializer, DispatchOrderStationEstimateSerializer, DispatchOrderTourCustomerSerializer, LocationHistoryRequestSerializer, LocationHistorySerializer, DriverCheckRequestSerializer, StationArrivalTimeSerializer, ConnectRequestSerializer, DailyDispatchOrderConnectListSerializer, DailyDispatchRegularlyConnectListSerializer, GetOffWorkDataSerialzier, GetOffWorkRequestSerializer, DispatchRegularlyConnectListSerializer, DispatchOrderConnectListSerializer, DispatchOrderConnectDetailSerializer, DispatchRegularlyConnectDetailSerializer, \
    ProblemOrderConnectListSerializer, ProblemRegularlyConnectListSerializer, ProblemOrderConnectDetailSerializer, ProblemRegularlyConnectDetailSerializer
from my_settings import SUNGHWATOUR_CRED_PATH, CRED_PATH
from itertools import chain
from operator import itemgetter

from firebase.fcm_message import send_message
from firebase_admin import firestore
from firebase.rpa_p_firebase import RpaPFirebase

from .twilio import generate_verification_code, send_verification_code
from django.core.cache import cache  # Django 캐시 사용

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

# 일일 배차 리스트
class DailyListDispatches(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, date):
        # 날짜 형식 검사
        try:
            datetime.strptime(date, "%Y-%m-%d")  # DATE_FORMAT이 "%Y-%m-%d" 형식이라고 가정
        except ValueError:
            return Response({
                'result': 'false',
                'data': '1',
                'message': {'error': 'Invalid date format'}
            }, status=status.HTTP_400_BAD_REQUEST)

        # 사용자 및 날짜 조건으로 정기 배차와 주문 배차 데이터 가져오기
        user = request.user
        regularly_dispatches = DispatchRegularlyConnect.objects.filter(departure_date__startswith=date, driver_id=user)
        order_dispatches = DispatchOrderConnect.objects.filter(departure_date__startswith=date, driver_id=user)

        # 데이터 직렬화
        regularly_serialized = DispatchRegularlyConnectListSerializer(regularly_dispatches, many=True).data
        order_serialized = DispatchOrderConnectListSerializer(order_dispatches, many=True).data

        # 두 리스트를 하나로 합친 후 departure_date(또는 departure_time) 기준으로 정렬
        combined_dispatches = list(chain(regularly_serialized, order_serialized))
        combined_dispatches.sort(key=itemgetter('departure_date'))  # departure_date로 정렬

        response_data = {
            'result': 'true',
            'data': combined_dispatches,
            'message': ''
        }

        return Response(response_data, status=status.HTTP_200_OK)

# 일일 배차 상세 조회
class DispatchDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        # 쿼리 파라미터에서 'id'와 'work_type' 가져오기
        dispatch_id = request.query_params.get('id')
        work_type = request.query_params.get('work_type')

        # 필수 파라미터가 없을 때 오류 처리
        if not dispatch_id or not work_type:
            return Response({
                'result': 'false',
                'data': 0,
                'message': 'id와 work_type 파라미터가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # work_type에 따라 다른 모델과 시리얼라이저를 선택
        try:
            if work_type == '출근':
                dispatch = get_object_or_404(DispatchRegularlyConnect, id=dispatch_id, work_type=work_type, driver_id=request.user)
                serializer_class = DispatchRegularlyConnectDetailSerializer
            elif work_type == '퇴근':
                dispatch = get_object_or_404(DispatchRegularlyConnect, id=dispatch_id, work_type=work_type, driver_id=request.user)
                serializer_class = DispatchRegularlyConnectDetailSerializer                
            elif work_type == '일반':
                dispatch = get_object_or_404(DispatchOrderConnect, id=dispatch_id, work_type=work_type, driver_id=request.user)
                serializer_class = DispatchOrderConnectDetailSerializer
            else:
                return Response({
                    'result': 'false',
                    'data': None,
                    'message': '유효하지 않은 work_type입니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 선택한 시리얼라이저로 직렬화
            serializer = serializer_class(dispatch, context={'work_type': work_type})
            
            # 성공 응답 구성
            return Response({
                'result': 'true',
                'data': serializer.data,
                'message': '성공적으로 데이터를 가져왔습니다.'
            }, status=status.HTTP_200_OK)
        
        except Http404:
            # get_object_or_404에서 발생하는 Http404 예외 처리
            return Response({
                'result': 'false',
                'data': None,
                'message': 'No matching DispatchOrderConnect or DispatchRegularlyConnect found for the given query.'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            # 기타 예상치 못한 오류 처리
            return Response({
                'result': 'false',
                'data': None,
                'message': f'오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 문제 있는 배차 리스트
class ProblemListDispatches(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, date):
        # 관리자와 팀장 권한 확인
        if request.user.role not in ["관리자", "팀장"] :
            return Response({
                'result': 'false',
                'data': None,
                'message': '권한이 없습니다.'
            }, status=status.HTTP_403_FORBIDDEN)

        # 날짜 형식 검사
        try:
            datetime.strptime(date, "%Y-%m-%d")  # DATE_FORMAT이 "%Y-%m-%d" 형식이라고 가정
        except ValueError:
            return Response({
                'result': 'false',
                'data': None,
                'message': {'error': 'Invalid date format'}
            }, status=status.HTTP_400_BAD_REQUEST)

        # 문제 있는 정기 배차와 일반 배차 가져오기
        regularly_dispatches = DispatchRegularlyConnect.objects.filter(departure_date__startswith=date, has_issue=True)
        order_dispatches = DispatchOrderConnect.objects.filter(departure_date__startswith=date, has_issue=True)

        # 데이터 직렬화
        regularly_serialized = ProblemRegularlyConnectListSerializer(regularly_dispatches, many=True).data
        order_serialized = ProblemOrderConnectListSerializer(order_dispatches, many=True).data

        # 두 리스트를 하나로 합친 후 departure_date 기준으로 정렬
        combined_dispatches = list(chain(regularly_serialized, order_serialized))
        combined_dispatches.sort(key=itemgetter('departure_date'))  # departure_date로 정렬

        response_data = {
            'result': 'true',
            'data': combined_dispatches,
            'message': ''
        }

        return Response(response_data, status=status.HTTP_200_OK)

# 문제 배차 상세 조회
class ProblemDispatchDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        # 관리자와 팀장 권한 확인
        if request.user.role not in ["관리자", "팀장"] :
            return Response({
                'result': 'false',
                'data': None,
                'message': '권한이 없습니다.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 쿼리 파라미터에서 'id'와 'work_type' 가져오기
        dispatch_id = request.query_params.get('id')
        work_type = request.query_params.get('work_type')

        # 필수 파라미터가 없을 때 오류 처리
        if not dispatch_id or not work_type:
            return Response({
                'result': 'false',
                'data': None,
                'message': 'id와 work_type 파라미터가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 배차 종류에 따라 모델 및 데이터를 가져옴
            if work_type in ['출근', '퇴근']:
                dispatch = get_object_or_404(DispatchRegularlyConnect, id=dispatch_id, has_issue=True)
                serializer_class = ProblemRegularlyConnectDetailSerializer

            elif work_type == '일반':
                dispatch = get_object_or_404(DispatchOrderConnect, id=dispatch_id, has_issue=True)
                serializer_class = ProblemOrderConnectDetailSerializer

            else:
                return Response({
                    'result': 'false',
                    'data': None,
                    'message': '유효하지 않은 work_type입니다.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 직렬화
            serializer = serializer_class(dispatch)
            response_data = serializer.data

            # 성공 응답 반환
            return Response({
                'result': 'true',
                'data': response_data,
                'message': '성공적으로 데이터를 가져왔습니다.'
            }, status=status.HTTP_200_OK)

        except Http404:
            # 배차가 없을 경우
            return Response({
                'result': 'false',
                'data': None,
                'message': '해당 배차를 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            # 기타 예외 처리
            return Response({
                'result': 'false',
                'data': None,
                'message': f'오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class LocationHistory(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        request_serializer = LocationHistoryRequestSerializer(data=request.GET)
        # id가 숫자가 아님
        if not request_serializer.is_valid():
            return StandardResponse.get_response(False, '1', request_serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        try:
            connect_id = request_serializer.validated_data['id']
            connect = DispatchRegularlyConnect.objects.get(id=connect_id)
            response_serializer = LocationHistorySerializer(connect)
            return StandardResponse.get_response(True, response_serializer.data, "", status.HTTP_200_OK)


        # 올바르지 않은 id
        except DispatchRegularlyConnect.DoesNotExist:
            error_message = {'id': "Invalid Id"}
            return StandardResponse.get_response(False, '2', error_message, status.HTTP_404_NOT_FOUND)
    
        except Exception as e:
            return StandardResponse.get_response(False, '3', {'error': f"{e}"}, status.HTTP_400_BAD_REQUEST)
            

    def post(self, request):
        try:
            connect = DispatchRegularlyConnect.objects.get(
                id=request.data.get('id')
            )
            
            serializer = LocationHistorySerializer(
                connect,
                data=request.data,
                partial=True  # 부분 업데이트 허용
            )
            
            if serializer.is_valid():
                serializer.save()
                return StandardResponse.get_response(True, serializer.data, "", status.HTTP_200_OK)
            
            return StandardResponse.get_response(False, "1", {"error": f"{serializer.errors}"}, status.HTTP_400_BAD_REQUEST)
        
        # 올바르지 않은 id
        except DispatchRegularlyConnect.DoesNotExist:
            return StandardResponse.get_response(False, '2', {"id": "Invalid Id"}, status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return StandardResponse.get_response(False, '3', {'error': f"{e}"}, status.HTTP_400_BAD_REQUEST)

class DailyGetOffWorkView(APIView):
    serializer_class = GetOffWorkRequestSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return StandardResponse.get_response(False, '1', {"error": str(serializer.errors)}, status.HTTP_400_BAD_REQUEST)
        
        try:
            checklist = EveningChecklist.objects.get(date=serializer.data['date'], member=request.user)
            # 배차 확인
            if serializer.data['status_type'] == EveningChecklist.STATUS_TYPE_CHOCIES[0]:
                checklist.tomorrow_check_submit_time = str(datetime.now())[11:16]
            # 퇴근
            elif serializer.data['status_type'] == EveningChecklist.STATUS_TYPE_CHOCIES[1]:
                checklist.get_off_submit_time = str(datetime.now())[11:16]
            checklist.save()
            data = EveningChecklistSerializer(checklist).data

            return StandardResponse.get_response(True, data, "", status.HTTP_200_OK)
        

        except EveningChecklist.DoesNotExist:
            return StandardResponse.get_response(False, '2', {"error": "EveningChecklist DoesNotExist"}, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return StandardResponse.get_response(False, '3', {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class DailyRoutineView(APIView):
    def get(self, request, date):
        try:
            datetime.strptime(date, DATE_FORMAT)
        except ValueError:
            return StandardResponse.get_response(False, "1", {"error": "Invalid date format"}, status.HTTP_400_BAD_REQUEST)

        user = request.user

        tasks = self.get_connect_list(date, user)
        get_off_work = self.get_get_off_work_data(date, user)
        info = self.get_current_task(tasks)

        data = {
            "status": info['status'],
            "info": info,
            "tasks": tasks,
            "get_off_work": get_off_work,
        }
        return StandardResponse.get_response(True, data, "", status.HTTP_200_OK)

    # 배차 데이터 불러오기
    def get_connect_list(self, date, user):
        regularly_connects, order_connects = DispatchConnectService.get_daily_connect_list(date, user)

        # 데이터 직렬화
        regularly_serialized = DailyDispatchRegularlyConnectListSerializer(regularly_connects, many=True).data
        order_serialized = DailyDispatchOrderConnectListSerializer(order_connects, many=True).data

        # 두 데이터 리스트 합치기
        combined_data = regularly_serialized + order_serialized

        # departure_date 기준으로 정렬
        combined_data = sorted(combined_data, key=lambda x: x["departure_date"])
        return combined_data
    
    def get_current_task(self, tasks):
        current_connect = DispatchConnectService.get_current_connect(tasks)
        if current_connect:
            return {
                "dispatch_id": current_connect['dispatch_id'],
                "departure_time": current_connect['departure_date'][11:16],
                "bus_id": current_connect['bus_id'],
                "bus_num": current_connect['bus_num'],
                "departure": current_connect['departure'],
                "status": current_connect['status'],
            }
        # 조건에 맞는 배차가 없는 경우
        return {
            "dispatch_id": "",
            "departure_time": "",
            "bus_id": "",
            "bus_num": "",
            "departure": "",
            "status": "",
        }

    
    # 퇴근 데이터 불러오기
    def get_get_off_work_data(self, date, user):
        try:
            evening_checklist = EveningChecklist.objects.get(date=date, member=user)
        except EveningChecklist.DoesNotExist:
            evening_checklist = EveningChecklist.create_new(date, user)
        return GetOffWorkDataSerialzier(evening_checklist).data
    

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

class DriverCheckView2(APIView):
    def post(self, request):
        request_serializer = DriverCheckRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return StandardResponse.get_response(False, "1", request_serializer.errors, status.HTTP_400_BAD_REQUEST)

        try:
            connect_id = request_serializer.validated_data['id']
            work_type = request_serializer.validated_data['work_type']

            if work_type == '출근' or work_type == '퇴근':
                driver_check = DriverCheck.objects.get(regularly_id=connect_id)
                connect = driver_check.regularly_id
            elif work_type == '일반':
                driver_check = DriverCheck.objects.get(order_id=connect_id)
                connect = driver_check.order_id
            else:
                return StandardResponse.get_response(False, "1", {"error": "work_type error"}, status.HTTP_400_BAD_REQUEST)
            # type에 따라 시간 저장
            time = request_serializer.validated_data['time']
            time_type = request_serializer.validated_data['type']

            # enum 활용해서 시간값 저장
            setattr(driver_check, ConnectStatusFieldMapping.DRIVER_CHECK_STATUS_FIELD_MAP[time_type], time)
            driver_check.save()
            # type값에 따라 connect의 다음 status로 변경
            connect.status = ConnectStatus.get_next_status(time_type)
            connect.save()

            # 운행종료일때 다음 배차의 has_issue 확인하여 status 다음 배차 status 변경 
            if time_type == ConnectStatus.END:
                self.set_next_status(connect, request.user)

            data = DriverCheckSerializer(driver_check).data
            data['current_status'] = connect.status
            return StandardResponse.get_response(True, data, "", status.HTTP_200_OK)


        # 올바르지 않은 id
        except DispatchRegularlyConnect.DoesNotExist:
            error_message = {'id': "Invalid Id"}
            return StandardResponse.get_response(False, '2', error_message, status.HTTP_404_NOT_FOUND)
        # 올바르지 않은 id
        except DispatchOrderConnect.DoesNotExist:
            error_message = {'id': "Invalid Id"}
            return StandardResponse.get_response(False, '2', error_message, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return StandardResponse.get_response(False, '3', {'error': f"{e}"}, status.HTTP_400_BAD_REQUEST)

    def set_next_status(self, connect, user):
        date = connect.departure_date[:10]
        regularly_connects, order_connects = DispatchConnectService.get_daily_connect_list(date, user)
        
        # 두 데이터 리스트 합치기
        combined_data = list(regularly_connects.values('departure_date', 'status', 'id', 'work_type')) + list(order_connects.values('departure_date', 'status', 'id', 'work_type'))
        # departure_date 기준으로 정렬
        combined_data = sorted(combined_data, key=lambda x: x["departure_date"])

        # 다음 진행할 배차 찾기
        next_connect = DispatchConnectService.get_current_connect(combined_data)
        if next_connect:
            if next_connect['work_type'] == "출근" or next_connect['work_type'] == "퇴근":
                driver_check = DriverCheck.objects.get(regularly_id=next_connect['id'])
                connect = DispatchRegularlyConnect.objects.get(id=next_connect['id'])
            # 일반
            else:
                driver_check = DriverCheck.objects.get(regularly_id=next_connect['id'])
                connect = DispatchOrderConnect.objects.get(id=next_connect['id'])

            # 다음 배차의 1시간, 20분 전 시간이 현재 배차의 운행시간과 겹치는 경우 has_issue 값을 False로 바꿔줌
            # 겹치지 않는 경우, has_issue 기본값이 True라서 아래 조건 통과하고 운행 준비부터 순차적으로 진행
            # 운행시작시간(1시간 전)에 문제가 없다면 운행일보 작성으로
            if not driver_check.drive_time_has_issue:
                connect.status = ConnectStatus.DRIVE_LOG_START
                connect.save()
            # 기상확인시간(1시간 30분 전)에 문제가 없다면 탑승 및 운행 시작으로
            elif not driver_check.wake_time_has_issue:
                connect.status = ConnectStatus.BOARDING
                connect.save()
        return 


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
        
        try:
            files = request.FILES.getlist('files', None)
            tmp_path = os.path.join(BASE_DIR, 'media/tmp')
            data['files'] = ','.join(upload_files(files, tmp_path, ConnectRefusal))
        except Exception as e:
            response = {
                'result' : 'false',
                'data' : '1',
                'message': {
                    'error' : f"File Save Error. {e}"
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

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

class StationCheckView(APIView):
    def post(self, request):
        serializer = StationArrivalTimeSerializer(data=request.data)
        if serializer.is_valid():
            station_arrival_time = serializer.save()
            station_arrival_time.creator = request.user
            station_arrival_time.save()
        else:
            return StandardResponse.get_response(False, "1", serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        # 운행 중이 아닐때 last='ture'이면 에러
        if station_arrival_time.regularly_connect_id.status != ConnectStatus.DRIVING:
            return StandardResponse.get_response(False, "2", {"error": "운행중이 아닙니다"}, status.HTTP_400_BAD_REQUEST)

        data = serializer.data
        # 마지막 정류장이면 Connect의 status 운행 중에서 운행 일보 작성으로 변경
        if request.data['is_last_station'] == "true":
            connect = station_arrival_time.regularly_connect_id
            connect.status = ConnectStatus.get_next_status(ConnectStatus.DRIVING)
            connect.save()
            data['current_status'] = connect.status

        return StandardResponse.get_response(True, data, "", status.HTTP_200_OK)
        
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
            return StandardResponse.get_response(False, '1', {'error' : 'invalid date format'}, status.HTTP_400_BAD_REQUEST)
        
        try:
            checklist = MorningChecklist.objects.filter(date=date).get(member=request.user)    
            serializer = MorningChecklistSerializer(checklist, data=data)
        except MorningChecklist.DoesNotExist:
            serializer = MorningChecklistSerializer(data=data)
        
        if serializer.is_valid():
            instance = serializer.save()
            instance.submit_check = True
            instance.submit_time = str(datetime.now())[11:16]
            instance.save()

            # 오늘 배차 모두 확인해서 도착시간과 다음 배차의 1시간 전, 20분 전 중복되는 부분 찾아서 has_issue 값 변경
            self.check_daily_connects(date, request.user)

            return StandardResponse.get_response(True, serializer.data, "", status.HTTP_200_OK)
        response = {
            'result': 'false',
            'data': '2',
            'message': {
                'error': serializer.errors
            }
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
    
    def check_daily_connects(self, date, user):
        regularly_connects, order_connects = DispatchConnectService.get_daily_connect_list(date, user)
        combined_data = list(regularly_connects.values('departure_date', 'arrival_date', 'id', 'work_type')) + list(order_connects.values('departure_date', 'arrival_date', 'id', 'work_type'))
        # departure_date 기준으로 정렬
        combined_data = sorted(combined_data, key=lambda x: x["departure_date"])

        # combined_data 순회하며 조건 확인
        for i in range(len(combined_data) - 1):  # 마지막 요소는 다음 배차가 없으므로 제외
            current_data = combined_data[i]
            next_data = combined_data[i + 1]
            
            current_arrival_date = datetime.strptime(current_data["arrival_date"], DATE_TIME_FORMAT)
            next_departure_date = datetime.strptime(next_data["departure_date"], DATE_TIME_FORMAT)

            # 다음 배차의 departure_date - 1시간 < 현재 배차의 arrival_date 조건
            if next_departure_date - timedelta(hours=1) <= current_arrival_date:
                if next_data['work_type'] == '출근' or next_data['work_type'] == '퇴근':
                    driver_check = DriverCheck.objects.get(regularly_id=next_data['id'])
                elif next_data['work_type'] == '일반':
                    driver_check = DriverCheck.objects.get(order_id=next_data['id'])
                driver_check.wake_time_has_issue = False
                print("")
                driver_check.save()

            # 다음 배차의 departure_date - 20분 < 현재 배차의 arrival_date 조건
            if next_departure_date - timedelta(minutes=20) <= current_arrival_date:
                driver_check.drive_time_has_issue = False
                driver_check.save()

        
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
            instance.checklist_submit_time = str(datetime.now())[11:16]
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
            instance.submit_time = str(datetime.now())[11:16]
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

class NewDrivingHistoryView(APIView):
    def get(self, request):
        
        serializer = ConnectRequestSerializer(data=request.GET)

        if not serializer.is_valid():
            return StandardResponse.get_response(False, '1', {'error' : 'invalid connect id'}, status.HTTP_400_BAD_REQUEST)

        id = self.request.GET.get('id')
        work_type = self.request.GET.get('work_type')

        try:
            if work_type == '출근' or work_type == '퇴근':
                connect = DispatchRegularlyConnect.objects.get(id=id)
                driving_history = DrivingHistory.objects.get(regularly_connect_id=id)
            else: # work_type == '일반'
                connect = DispatchOrderConnect.objects.get(id=id)
                driving_history = DrivingHistory.objects.get(order_connect_id=id)
            
            data = DrivingHistorySerializer(driving_history).data
            return StandardResponse.get_response(True, data, "", status.HTTP_200_OK)

        except DrivingHistory.DoesNotExist:
            driving_history = DrivingHistory(
                member = request.user,
                creator = request.user,
            )
            if work_type == '출근' or work_type == '퇴근':
                driving_history.regularly_connect_id = id
            else:
                driving_history.order_connect_id = id
            driving_history.date = connect.departure_date[:10]
            driving_history.save()
        except DispatchOrderConnect.DoesNotExist:
            return StandardResponse.get_response(False, '2', {'error' : 'Invalid connect id'}, status.HTTP_404_NOT_FOUND)
        except DispatchRegularlyConnect.DoesNotExist:
            return StandardResponse.get_response(False, '2', {'error' : 'Invalid connect id'}, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return StandardResponse.get_response(False, '3', {'error' : f'{e}'}, status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        data = request.data.copy()
        data['member'] = request.user.id
        data['creator'] = request.user.id
        
        id = data['id']
        work_type = data['work_type']

        if not (work_type and id):
            return StandardResponse.get_response(False, '1', {'error' : 'id and work_type'}, status.HTTP_400_BAD_REQUEST)

        try:
            if work_type == '출근' or work_type == '퇴근':
                data['regularly_connect_id'] = id
                connect = DispatchRegularlyConnect.objects.get(id=id)
                driving_history = DrivingHistory.objects.get(regularly_connect_id=id)
            elif work_type == '일반':
                data['order_connect_id'] = id
                connect = DispatchOrderConnect.objects.get(id=id)
                driving_history = DrivingHistory.objects.get(order_connect_id=id)
            else:
                return StandardResponse.get_response(False, '1', {'error' : 'id and work_type'}, status.HTTP_400_BAD_REQUEST)
            date = connect.departure_date[:10]

        # id 에러
        except DispatchOrderConnect.DoesNotExist:
            return StandardResponse.get_response(False, '2', {'error' : 'Invalid connect id'}, status.HTTP_404_NOT_FOUND)
        except DispatchRegularlyConnect.DoesNotExist:
            return StandardResponse.get_response(False, '2', {'error' : 'Invalid connect id'}, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return StandardResponse.get_response(False, '3', {'error' : str(e)}, status.HTTP_400_BAD_REQUEST)

        serializer = DrivingHistorySerializer(driving_history, data=data)
        
        if serializer.is_valid():
            instance = serializer.save()
            instance.submit_check = True
            instance.submit_time = str(datetime.now())[11:16]
            instance.date = date
            instance.save()
            data = serializer.data

            current_status = connect.status
            # connect status 다음 상태 값으로 변경
            if current_status == ConnectStatus.DRIVE_LOG_START or current_status == ConnectStatus.DRIVE_LOG_END:
                connect.status = ConnectStatus.get_next_status(current_status)
                connect.save()
            
            data['current_status'] = connect.status
            return StandardResponse.get_response(True, data, "", status.HTTP_200_OK)
        return StandardResponse.get_response(False, '4', serializer.errors, status.HTTP_400_BAD_REQUEST)

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
                #data = {
                #    'member' : member.name,
                #    'member_id' : member.id,
                #    'current_count' : 0,
                #    'total_count' : 0,
                #    'bus' : '',
                #    'route' : '',
                #    'departure_time' : '',
                #    'check1' : '',
                #    'check2' : '',
                #    'check3' : '',
                #}
                #data_list.append(data)
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

            check1 = ''
            check2 = ''
            check3 = ''
            if current_time > check_time1 and not driver_check.wake_time:
                check1 = 'false'
            elif driver_check.wake_time:
                check1 = 'true'
            if current_time > check_time2 and not driver_check.drive_time:
                check2 = 'false'
            elif driver_check.drive_time:
                check2 = 'true'
            if current_time > check_time3 and not driver_check.departure_time:
                check3 = 'false'
            elif driver_check.departure_time:
                check3 = 'true'

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

# rpa-p
class EstimateView(APIView):
    def post(self, request):

        departure = request.data['departure']['name']
        arrival = request.data['arrival']['name']

        stopover = []
        for item in request.data["stopover"]:
            stopover.append(item['name'])
        
        data = {
            "departure" : departure,
            "arrival" : arrival,
            "departure_date" : request.data['departureDate'],
            "arrival_date" : request.data['arrivalDate'],
            "bus_cnt" : request.data['busCount'],
            "bus_type" : request.data['busType'],
            "customer" : request.data['signedName'],
            "customer_phone" : request.data['phone'],
            "contract_status" : "보류",
            "operation_type" : f"{request.data['kindsOfEstimate']} ({request.data['operationType']})" if request.data['operationType'] else request.data['kindsOfEstimate'],
            "reservation_company" : "RPA-P",
            "operating_company" : "성화투어",
            "price" : request.data['price'],
            "driver_allowance" : 0,
            # "option" : "",
            # "cost_type" : "",
            # "bill_place" : "",
            # "collection_type" : "",
            "payment_method" : request.data['payWay'],
            "VAT" : "n",
            # "total_price" : ,
            # "ticketing_info" : request.data[''],
            # "order_type" : request.data[''],
            "references" : f"{TODAY} RPA-P로 예약됨",
            # "driver_lease" : request.data[''],
            # "vehicle_lease" : request.data[''],
            "route" : f"{departure} ▶ {arrival}",
            "distance" : request.data['distance'],
            "time" : request.data['duration'],
            # "distance_list" : request.data[''],
            # "time_list" : request.data[''],
            "creator" : request.user.id
        }

        #     # 전화번호 인증이 완료되었는지 확인
        # if not cache.get(f"verified_{request.data['phone']}"):
        #     return Response({
        #         'result': 'false',
        #         'message': '전화번호 인증이 완료되지 않았습니다.'
        #     }, status=status.HTTP_400_BAD_REQUEST)

        
        serializer = DispatchOrderEstimateSerializer(data=data)
        if serializer.is_valid():
            order = serializer.save()
        else:
            return Response({
                'result': 'false',
                'data': '1',
                'message': {
                    'error' : serializer.errors
                }
            }, 
            status=status.HTTP_400_BAD_REQUEST
            )

        station_list = request.data['stopover'] if request.data['stopover'] else []
        # station_list.append(request.data['departure'])
        # station_list.append(request.data['arrival'])
        station_list = sorted(station_list, key=lambda x: x['index'])

        for station_data in station_list:
            data = {
                "order_id" : order.id,
                "station_name" : station_data['name'],
                "place_name" : station_data['name'],
                "address" : station_data['address'],
                "longitude" : station_data['longitude'],
                "latitude" : station_data['latitude'],
                # "time" : ,
                # "delegate" : ,
                # "delegate_phone" : ,
                "creator" : request.user.id
            }
            station_serializer = DispatchOrderStationEstimateSerializer(data=data)
            if station_serializer.is_valid():
                station_serializer.save()
            else:
                return Response({
                    'result': 'false',
                    'data': '2',
                    'message': {
                        'error' : station_serializer.errors
                    }
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # init firebase
        estimate = {
            "departure" : departure,
            "arrival" : arrival,
            "departureDate" : request.data['departureDate'],
            "arrivalDate" : request.data['arrivalDate'],
            "stopover" : stopover,
            "busCount" : request.data['busCount'],
            "busType" : request.data['busType'],
            "signedName" : request.data['signedName'],
            "phone" : request.data['phone'],
            "kindsOfEstimate" : request.data['kindsOfEstimate'],
            "operationType" : request.data['operationType'],
            "price" : request.data['price'],
            "payWay" : request.data['payWay'],
            "distance" : request.data['distance'],
            "duration" : request.data['duration'],
            "number" : request.data["number"],
            "isCompletedReservation" : request.data["isCompletedReservation"],
            "isConfirmedReservation" : request.data["isConfirmedReservation"],
            "isPriceChange" : request.data["isPriceChange"],
            "isEstimateApproval" : request.data["isEstimateApproval"],
            "departureIndex" : request.data["departureIndex"],
        }
        firebase = RpaPFirebase()
        try:
            estimate_path, estimate_uid = firebase.add_estimate(estimate, request.data['uid'], station_list)
            order.firebase_uid = estimate_uid
            order.firebase_path = estimate_path
            order.save()
        except Exception as e:
            response = {
                'result': 'false',
                'data': '3',
                'message': {
                    'error' : f"{e}"
                }
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = {
            'result': 'true',
            'data': estimate_uid,
            'message': ''
        }

        send_admin_notification(order, "TRP에서 배차 확정을 해주세요")


        return Response(response, status=status.HTTP_200_OK)

def send_admin_notification(order, title):
    target_list = []
    try:
        target_list.append(Member.objects.get(use="사용", authority__lte=1, name="김인숙"))
        target_list.append(Member.objects.get(use="사용", authority__lte=1, name="이세명"))
        target_list.append(Member.objects.get(use="사용", authority__lte=1, name="박유진"))
        target_list.append(Member.objects.get(use="사용", authority__lte=1, name="엄성환"))

    except Exception as e:
        response = {
            'result': 'false',
            'data': '4',
            'message': {
                'error' : f"{e}"
            }
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    for target in target_list:
        if target.token:
            print(target.name)
            send_message(title, f"{order.route}\n{order.departure_date} ~ {order.arrival_date}", target.token, None)


class EstimateReservationConfirmView(APIView):
    def post(self, request):
        user_uid = request.data.get('userUid')
        estimate_uid = request.data.get("estimateUid")

        try:
            order = DispatchOrder.objects.get(firebase_uid=estimate_uid)
            order.contract_status = "예약확정"
            order.save()
            #TODO rpad 관리자한테 알림 보내기
        except Exception as e:
            response = {
                'result': 'false',
                'data': '1',
                'message': {
                    'error' : f"{e}"
                }
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        firebase = RpaPFirebase()
        edit_type = "isConfirmedReservation"
        path = firebase.get_doc_path(estimate_uid, user_uid)
        estimate_data = firebase.edit_value(path, edit_type, True)

        response = {
            'result': 'true',
            'data': estimate_data,
            'message': ''
        }

        send_admin_notification(order, "계약금 입금 확인 후 TRP에서 계약현황 확정을 해주세요")
        return Response(response, status=status.HTTP_200_OK)

class EstimateContract(APIView):
    template_name = 'estimate_print.html'

    def set_order(self, request):
        estimate_uid = request.GET.get("estimateUid")
        order = DispatchOrder.objects.get(firebase_uid=estimate_uid)
        return order

    def set_context(self, request, order):
        context = model_to_dict(order)
        context['customer'] = order.customer
        context['customer_phone'] = order.customer_phone
        context['contract_date'] = datetime.strftime(order.pub_date, "%Y년 %m월 %d일")
        context['estimate_date'] = datetime.strftime(datetime.strptime(order.departure_date[:10], "%Y-%m-%d"), "%Y년 %m월 %d일")
        context['total_price'] = f"{(int(context['price']) * int(context['bus_cnt'])):,}"
        context['VAT'] = "VAT 포함" if context['VAT'] == "y" else "VAT 미포함"
        context['order'] = order
        context['price'] = f"{int(order.price):,}"
        # context['price_per_person'] = context['price'] / 
        context['vehicle_list'] = []
        for connect in order.info_order.all():
            context['vehicle_list'].append(f"{connect.bus_id.vehicle_num0} {connect.bus_id.vehicle_num}")
            
        context['station_list'] = []
        for station in order.station.all():
            context['station_list'].append(f"{station.station_name}")
        
        context['deposit'] = int(int(order.price) / 10)
        
        return context

    def get(self, request):
        try:
            order = self.set_order(request)
            context = self.set_context(request, order)
            
            # firebase = RpaPFirebase()
            # number = firebase.get_value(order.firebase_path, "number")
            return render(request, self.template_name, context)
        except Exception as e:
            response = {
                'result': 'false',
                'data': '1',
                'message': {
                    'error' : f"{e}"
                }
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

class TourContract(EstimateContract):
    template_name = 'tour_print.html'
    def set_order(self, request):
        tour_uid = request.GET.get("tourUid")
        tour = DispatchOrderTour.objects.get(firebase_uid=tour_uid)
        
        return tour.order_id
    
    def set_context(self, request, order):
        context = super().set_context(request, order)

        tour_uid = request.GET.get("tourUid")
        phone = request.GET.get("phone")
        tour = DispatchOrderTour.objects.get(firebase_uid=tour_uid)

        customer = DispatchOrderTourCustomer.objects.filter(tour_id=tour).filter(phone=phone).first()
        context['customer'] = customer.name
        context['customer_phone'] = customer.phone
        context['price_per_person'] = f"{int(tour.price):,}"
        context['bank'] = customer.bank
        return context
    def set_customer(self, request, order, context):
        
        return context



class TourView(APIView):
    def post(self, request):
        tour_uid = request.data.get("tour_uid")
        data = request.data.copy()
        

        try:
            tour = DispatchOrderTour.objects.get(firebase_uid=tour_uid)
            data['tour_id'] = tour.id
            data['creator'] = request.user.id
            if tour.max_people <= tour.tour_customer.count():
                response = set_response_false('1', {'error': "최대 인원수를 초과했습니다"})
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # tour가 없을 경우
        except Exception as e:
            response = set_response_false('2', {'error': f"{e}"})
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        tour_customer = DispatchOrderTourCustomerSerializer(data=data)
        if tour_customer.is_valid():
            tour_customer.save()

            response = set_response_true(tour_customer.data)
            return Response(response, status=status.HTTP_200_OK)
        response = set_response_false('3', {'error': f"{tour_customer.errors}"})
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        phone = request.GET.get("phone")

        try:
            customer_list = DispatchOrderTourCustomer.objects.filter(phone=phone)
            response = set_response_true(DispatchOrderTourCustomerSerializer(customer_list, many=True).data)
            
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response = set_response_false('1', {'error': f"{e}"})
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 전화번호 인증 코드 전송
@api_view(['POST'])
@permission_classes([AllowAny])
def send_code(request) :
    customer_phone = request.data.get('customer_phone')

    if not customer_phone :
        response = {
            'result' : 'false',
            'data': '1',
            'message' : '전화번호를 입력해주세요'
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 인증 코드 생성 및 전송
        verification_code = generate_verification_code()
        send_verification_code(customer_phone, verification_code)

        # 인증 코드를 캐시에 저장 (5분 동안 유지)
        cache.set(customer_phone, verification_code, timeout=300) 
        

        response = {
            'result': 'true',
            'data': '0',
            'message': '인증 코드가 성공적으로 전송되었습니다.'
        }
        return Response(response, status=status.HTTP_200_OK)
    
    except Exception as e:
        response = {
            'result': 'false',
            'data': '2',
            'message': str(e)           
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
        

# 전화번호 인증 코드 검증 
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_code(request):
    customer_phone = request.data.get('customer_phone')
    verification_code = request.data.get('verification_code')

    if not customer_phone or not verification_code:
        
        return Response({
            'result': 'false',
            'data': '1',
            'message': '전화번호와 인증 코드를 모두 입력해주세요.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # 캐시에서 저장된 인증 코드 가져오기
    stored_code = cache.get(customer_phone)

    if stored_code is None:
        
        return Response({
            'result': 'false',
            'data': '2',
            'message': '인증 코드가 만료되었거나 잘못된 전화번호입니다.'
        }, status=status.HTTP_400_BAD_REQUEST)

    if verification_code == stored_code:
        cache.set(f"verified_{customer_phone}", True, timeout=3600)  # 인증 완료 상태 캐시에 저장
        # 인증 성공 처리
        return Response({
            'result': 'true',
            'data': '0',
            'message': '인증이 성공적으로 완료되었습니다.'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'result': 'false',
            'data': '3',
            'message': '잘못된 인증 코드입니다.'
        }, status=status.HTTP_400_BAD_REQUEST)

# async def do_async():
#     try:
#         await fetch_firestore_data()
#         print("success")
#     except Exception as e:
#         print("ERROR", e)
    

# async def fetch_firestore_data():
#     db = firestore.Client()
#     print("TEST", db)
    
#     # sync_to_async를 사용하여 동기 메서드 비동기 호출
#     await sync_to_async(db.collection("cities2").document("LA").set)({"test": "test"})
