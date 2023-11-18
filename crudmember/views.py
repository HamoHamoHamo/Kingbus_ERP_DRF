from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from trp_drf.pagination import Pagination

from .models import Client
from .serializers import ClientListSerializer


class ClientListView(ListAPIView):
    queryset = Client.objects.all().order_by('name')
    serializer_class = ClientListSerializer
    pagination_class = Pagination

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        
        queryset = super().get_queryset()
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
                'client_list': response.data['results'],
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