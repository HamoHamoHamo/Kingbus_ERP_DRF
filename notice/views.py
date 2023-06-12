from django.shortcuts import get_object_or_404
from django.http import Http404, JsonResponse
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from trp_drf.settings import DATE_FORMAT ,TODAY
from .models import Notice, NoticeFile, NoticeComment, NoticeViewCnt
from .serializers import NoticeSerializer, NoticeListSerializer, CommentSerializer
from humanresource.models import Member
from trp_drf.pagination import Pagination

class NoticeListView(ListAPIView):
    queryset = Notice.objects.filter(kinds='driver').order_by('-pub_date')
    serializer_class = NoticeListSerializer
    pagination_class = Pagination

class NoticeDetailView(APIView):
    def get(self, request, id):
        queryset = get_object_or_404(Notice, id=id)
        response = NoticeSerializer(queryset).data
        return Response(response, status=status.HTTP_200_OK)
    
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

