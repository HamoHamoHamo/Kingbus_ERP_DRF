from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from . import views


urlpatterns = [
    path('client', views.ClientListView.as_view()),
    path('gasstation', views.GasStationListView.as_view()),
    path('garage', views.GarageListView.as_view()),
    
]