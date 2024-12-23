from django.shortcuts import get_object_or_404, render
from django.http import Http404, JsonResponse
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from trp_drf.settings import DATE_FORMAT ,TODAY
from .models import Notice, NoticeFile, NoticeComment, NoticeViewCnt
from .serializers import NoticeSerializer, NoticeListSerializer, CommentSerializer, NoticeViewCntSerializer
from humanresource.models import Member
from trp_drf.pagination import Pagination
from rest_framework.permissions import IsAuthenticated

class NoticeListView(ListAPIView):
    queryset = Notice.objects.filter(kinds='driver').order_by('-pub_date')
    serializer_class = NoticeListSerializer
    pagination_class = Pagination

class NoticeDetailView(APIView):
    def get(self, request, id):
        queryset = get_object_or_404(Notice, id=id)
        response = NoticeSerializer(queryset, context={'request': request}).data
        return Response(response, status=status.HTTP_200_OK)

class NoticeAsReadAPIView(APIView):
    def post(self, request):
        notice_id = request.data.get('notice_id')

        if not notice_id:
            return Response({
                'result': 'false',
                "message": "공지 ID가 필요합니다."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 공지 존재 여부
        try:
            notice = Notice.objects.get(id=notice_id)
        except Notice.DoesNotExist:
            return Response({
                'result': 'false',
                "message": "해당 공지를 찾을 수 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)

        # 이미 읽음 여부
        user = request.user
        if NoticeViewCnt.objects.filter(notice_id=notice, user_id=user).exists():
            return Response({
                'result': 'false',
                "message": "이미 읽은 공지입니다."
            }, status=status.HTTP_200_OK)

        # 읽음 처리
        data = {'notice_id': notice.id, 'user_id': user.id}
        serializer = NoticeViewCntSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                'result': 'true',
                "message": "공지 읽음 처리가 완료되었습니다."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CommentView(APIView):
    def post(self, request):
        data = request.data.copy()
        data['creator'] = request.user.id
        serializer = CommentSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            comment = serializer.save()
            response = {
                'data' : serializer.data,
                'success': True,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Request Body Error."}, status=status.HTTP_409_CONFLICT)

    def delete(self, request):
        comment = get_object_or_404(NoticeComment, id=request.data['id'])
        if (comment.creator == request.user):
            comment.delete()
            response = {
                'success' : True
            }
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response({'success': False}, status=status.HTTP_403_FORBIDDEN)

def approval_rule_print(request):
    return render(request, "notice/approval_rule_print.html")
def roll_call_rule_print(request):
    return render(request, "notice/roll_call_rule_print.html")
def driver_rule_print(request):
    return render(request, "notice/driver_rule_print.html")
def manager_rule_print(request):
    return render(request, "notice/manager_rule_print.html")
def field_manager_rule_print(request):
    return render(request, "notice/field_manager_rule_print.html")
def personnel_committee_rule_print(request):
    return render(request, "notice/personnel_committee_rule_print.html")