from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from trp_drf.pagination import Pagination

from .models import Client, Category
from .serializers import ClientListSerializer, CategoryListSerializer


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

class GasStationListView(ListAPIView):
    queryset = Category.objects.filter(type='주유장소').order_by('category')
    serializer_class = CategoryListSerializer
    pagination_class = Pagination

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        
        queryset = super().get_queryset()
        if search:
            return queryset.filter(category__contains=search)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        data = {
            'result': 'true',
            'data': {
                'count': response.data['count'],
                'next': response.data['next'],
                'previous': response.data['previous'],
                'gas_station_list': response.data['results'],
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

class GarageListView(ListAPIView):
    queryset = Category.objects.filter(type='차고지').order_by('category')
    serializer_class = CategoryListSerializer
    pagination_class = Pagination

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        
        queryset = super().get_queryset()
        if search:
            return queryset.filter(category__contains=search)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        data = {
            'result': 'true',
            'data': {
                'count': response.data['count'],
                'next': response.data['next'],
                'previous': response.data['previous'],
                'garage_list': response.data['results'],
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