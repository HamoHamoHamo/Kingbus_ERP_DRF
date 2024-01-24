from django.urls import path
from . import views

urlpatterns = [
    path('', views.VehicleListView.as_view()),
    path('/refueling', views.RefuelingView.as_view()),
    path('/checklist/daily/<str:date>', views.DailyChecklistView.as_view()),
    path('/checklist/weekly/<str:date>', views.WeeklyChecklistView.as_view()),
    path('/checklist/equipment/<str:date>', views.EquipmentChecklistView.as_view()),
]