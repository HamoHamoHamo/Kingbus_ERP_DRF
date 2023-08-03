from django import dispatch
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from rest_framework_simplejwt.views import TokenRefreshView

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import UserLoginSerializer
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
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            status_code = status.HTTP_200_OK

            response = {
                'success': True,
                'statusCode': status_code,
                'message': 'User logged in successfully',
                'access': serializer.validated_data['access'],
                'refresh': serializer.validated_data['refresh'],
                'authenticatedUser': {
                    'user_id': serializer.validated_data['user_id'],
                    #name 추가
                    'name': serializer.validated_data['name'],
                    'role': serializer.validated_data['role']
                }
            }
            return Response(response, status=status_code)

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