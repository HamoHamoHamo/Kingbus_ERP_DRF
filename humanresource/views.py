from django import dispatch
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from my_settings import MAINTENANCE
from trp_drf.pagination import Pagination

from .serializers import UserLoginSerializer, MemberListSerializer, MemberSerializer
from .models import Member

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
    
class MemberListView(APIView):
    def get(self, request):
        try:
            data = {}
            data['member_list'] = Member.objects.filter(use='사용').exclude(role='임시').exclude(role='최고관리자').values('name', 'phone_num', 'role')
            response = {
                'result' : 'true',
                'data' : data,
                'message' : ''
            }
        except Exception as e:
            response = {
                'result' : 'false',
                'data' : 1,
                'message' : {
                    'error' : str(e)
                }
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response, status=status.HTTP_200_OK)
       
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