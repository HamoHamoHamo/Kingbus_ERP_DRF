from django.urls import path
from . import views

urlpatterns = [
    path('', views.VehicleListView.as_view()),
    path('/refueling', views.RefuelingView.as_view()),
]