from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from my_settings import MAINTENANCE
from trp_drf.pagination import Pagination
from trp_drf.settings import DATE_FORMAT
from django.http import Http404, HttpResponse, HttpResponseNotAllowed

from .serializers import UserLoginSerializer, MemberListSerializer, MemberSerializer
from .models import Member, Salary, SalaryChecked
from dispatch.models import DispatchRegularlyConnect, DispatchOrderConnect

WEEK = ['(월)', '(화)', '(수)', '(목)', '(금)', '(토)', '(일)', ]
TODAY = str(datetime.now())[:10]

class UserLoginView(APIView):
    serializer_class = UserLoginSerializer
    permission_classes = (AllowAny,)

    #def get(self, request):
    #    username = request.GET.get('username')
    #    if username is not None:
    #        # if 'username' in request.GET:
    #        if len(username)>=4:
    #            try:
    #                Member.objects.get(username=username)
    #                return Response({'result':'exists'},status=status.HTTP_409_CONFLICT)
    #            except ObjectDoesNotExist:
    #                return Response({'result':'not exists'},status=status.HTTP_202_ACCEPTED)
    #    return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=False)

        if valid:
            status_code = status.HTTP_200_OK
            response = {
                'result' : 'true',
                'data' : {
                    'access': serializer.validated_data['access'],
                    'refresh': serializer.validated_data['refresh'],
                    'authenticatedUser': {
                        'user_id': serializer.validated_data['user_id'],
                        #name 추가
                        'name': serializer.validated_data['name'],
                        'role': serializer.validated_data['role']
                    }
                },
                'message': '',
            }
            return Response(response, status=status_code)
        data = 1 if 'non_field_errors' in serializer.errors else 2
        sta = status.HTTP_200_OK if 'non_field_errors' in serializer.errors else status.HTTP_400_BAD_REQUEST
        response = {
            'result' : 'false',
            'data' : data,
            'message': serializer.errors,
        }
        return Response(response, status=sta)


class Notification(APIView):
    def patch(self, request):
        try:
            user = request.user
            token = request.data['token']
            user.token = token
            user.save()
            return Response({
                'result': 'true',
                'data': {
                    'token': user.token
                },
                'message': ''
            })
        except Exception as e:
            return Response({
                'result': 'false',
                'data': 1,
                'message': {
                    'detail': str(e)
                }
            })

class MaintenanceView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            res = {
                'result' : 'true',
                'data' : MAINTENANCE,
                'message' : ''
            }
        except Exception as e:
            res = {
                'result' : 'false',
                'data' : 1,
                'message' : {
                    'error' : str(e)
                }
            }
            return Response(res, status=status.HTTP_400_BAD_REQUEST)
        return Response(res, status=status.HTTP_200_OK)
    
class MemberListView(ListAPIView):
    queryset = Member.objects.filter(use='사용').exclude(role='임시').exclude(role='최고관리자').order_by('authority', 'name')
    serializer_class = MemberListSerializer
    pagination_class = Pagination

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        separate_role = self.request.GET.get('separate_role', '')
        
        queryset = super().get_queryset()
        if separate_role == '관리자':
            queryset = queryset.filter(role='관리자')
        if separate_role == '운전원':
            queryset = queryset.filter(Q(role='팀장')|Q(role='운전원'))
        if separate_role == '용역':
            queryset = queryset.filter(role='용역')
        if search:
            return queryset.filter(name__contains=search)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        data = {
            'result': 'true',
            'data': {
                'count': response.data['count'],
                'next': response.data['next'],
                'previous': response.data['previous'],
                'member_list': response.data['results'],
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

class LoginMemberView(APIView):
    def get(self, request):
        user = request.user
        data = MemberSerializer(user).data
        response = {
            'result' : 'true',
            'data' : data,
            'message' : '',
        }
        return Response(response, status=status.HTTP_200_OK)

#https://stackoverflow.com/questions/55416471/how-to-resolve-assertionerror-accepted-renderer-not-set-on-response-in-django
# api_view, renderer_classes 넣어야 됨 위 링크 참고
@api_view(('GET', 'POST'))
#@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def salary_detail(request):
    member_id = request.user.id
    month = request.GET.get('date', TODAY[:7])

    if request.method == 'POST':
        try:
            salary = Salary.objects.filter(member_id=member_id).get(month=month)
        except Exception as e:
            response = {
                'result' : 'false',
                'data' : '1',
                'message' : {
                    'error' : f"{e}"
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            salary_checked = salary.salary_checked
            salary_checked.save()
        except Exception as e:
            salary_checked = SalaryChecked(salary = salary, creator = request.user)
            salary_checked.save()

        response = {
            'result' : 'true',
            'data' : {
                'creator' : member_id,
                'updated_at' : str(salary_checked.updated_at),
                'date' : salary.month
            },
            'message' : '',
        }
        return Response(response, status=status.HTTP_200_OK)

    if request.method == "GET":
        try:
            datetime.strptime(month+'-01', DATE_FORMAT)
        except ValueError:
            response = {
                'result' : 'false',
                'data' : 1,
                'message' : {
                    'error' : 'Invalid month',
                },
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        # try:
        #     category_date = Category.objects.get(type='급여지급일').category
        #     if category_date == '말일':
        #         salary_date = datetime.strftime(datetime.strptime(month+'-01', DATE_FORMAT) + relativedelta(months=1) - timedelta(days=1), DATE_FORMAT)
        #     else:
        #         salary_date = f'{month}-{category_date}'
        # except Category.DoesNotExist:
        #     salary_date = ''
        
        member_list = []
        
        member = get_object_or_404(Member, id=member_id)
        last_date = datetime.strftime(datetime.strptime(month+'-01', DATE_FORMAT) + relativedelta(months=1) - timedelta(days=1), DATE_FORMAT)[8:10]

        attendance_list = [''] * int(last_date)
        leave_list = [''] * int(last_date)
        order_list = [''] * int(last_date)
        order_price_list = [0] * int(last_date)
        attendance_price_list = [0] * int(last_date)
        leave_price_list = [0] * int(last_date)
        week_list = []

        order_cnt = 0
        attendance_cnt = 0
        leave_cnt = 0
        
        total_list = [0] * int(last_date)
        work_cnt = 0
        

        salary = Salary.objects.filter(member_id=member).get(month=month)
        meal = salary.meal
        payment_date = salary.payment_date
        if payment_date == '말일':
            salary_date = datetime.strftime(datetime.strptime(month+'-01', DATE_FORMAT) + relativedelta(months=1) - timedelta(days=1), DATE_FORMAT)
        else:
            salary_date = f'{month}-{payment_date}'

        additional = salary.additional_salary.all()
        deduction = salary.deduction_salary.all()

        connects = DispatchOrderConnect.objects.filter(departure_date__range=(f'{month}-01 00:00', f'{month}-{last_date} 24:00')).filter(driver_id=member)
        order_cnt = connects.count()
        for connect in connects:
            c_date = int(connect.departure_date[8:10]) - 1
            if not order_list[c_date]:
                order_list[c_date] = []
            order_list[c_date].append([connect.order_id.departure, connect.order_id.arrival])
            
        # if connects:
            if connect.payment_method == 'n':
                order_price_list[c_date] += int(connect.driver_allowance)
                total_list[c_date] += int(connect.driver_allowance)

        attendances = DispatchRegularlyConnect.objects.filter(departure_date__range=(f'{month}-01 00:00', f'{month}-{last_date} 24:00')).filter(work_type='출근').filter(driver_id=member)
        attendance_cnt = attendances.count()
        for attendance in attendances:            
            c_date = int(attendance.departure_date[8:10]) - 1
            if not attendance_list[c_date]:
                attendance_list[c_date] = []
            attendance_list[c_date].append([attendance.regularly_id.departure, attendance.regularly_id.arrival])

            attendance_price_list[c_date] += int(attendance.driver_allowance)
        # if attendances:
            total_list[c_date] += int(attendance.driver_allowance)

        leaves = DispatchRegularlyConnect.objects.filter(departure_date__range=(f'{month}-01 00:00', f'{month}-{last_date} 24:00')).filter(work_type='퇴근').filter(driver_id=member)
        leave_cnt = leaves.count()
        for leave in leaves:
            c_date = int(leave.departure_date[8:10]) - 1
            if not leave_list[c_date]:
                leave_list[c_date] = []
            leave_list[c_date].append([leave.regularly_id.departure, leave.regularly_id.arrival])
        
            leave_price_list[c_date] += int(leave.driver_allowance)
        # if leaves:
            total_list[c_date] += int(leave.driver_allowance)


        for i in range(int(last_date)):
            check = 0

            if i + 1 < 10:
                date = f'{month}-0{i+1}'
            else:
                date = f'{month}-{i+1}'

            week_list.append(WEEK[datetime.strptime(date, DATE_FORMAT).weekday()])

            if check == 1:
                work_cnt += 1

        total_cnt = leave_cnt + attendance_cnt + order_cnt
        member_list.append({
            'order_list': order_list,
            'attendance_list': attendance_list,
            'leave_list': leave_list,
            'order_cnt': order_cnt,
            'total_cnt': total_cnt,
            'attendance_cnt': attendance_cnt,
            'leave_cnt': leave_cnt,
            'order_price_list': order_price_list,
            'attendance_price_list': attendance_price_list,
            'leave_price_list': leave_price_list,
            'salary': salary,
            'member': member,
            'week_list': week_list,
            'total_list': total_list,
            'work_cnt': work_cnt,
            'additional': additional,
            'deduction': deduction,
            'meal': meal,
            'salary_date': salary_date,
        })
            
        context = {
            'member_list': member_list,
            'month': month
        }
        return render(request, 'salary_detail.html', context)

    else:
        return HttpResponseNotAllowed(['post', 'get'])

class TokenRefreshView(jwt_views.TokenRefreshView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=False)
        except TokenError as e:
            return Response({
                'result' : 'false',
                'data' : 1,
                'message' : {"token" : ["Token is invalid or expired"]},
            }, status=status.HTTP_401_UNAUTHORIZED)
        if serializer.is_valid(raise_exception=False):
            response = {
                'result' : 'true',
                'data' : serializer.validated_data,
                'message' : '',
            }
            return Response(response, status=status.HTTP_200_OK)
        else:
            response = {
                'result' : 'false',
                'data' : 2,
                'message' : serializer.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)