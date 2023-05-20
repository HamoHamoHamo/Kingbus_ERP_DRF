from django.urls import path
from . import views


urlpatterns = [
    path('monthly/<str:month>', views.MonthlyDispatches.as_view()),
    path('daily/<str:date>', views.DailyDispatches.as_view()),
    path('check', views.DriverCheckView.as_view()),
    path('connect/check', views.ConnectCheckView.as_view()),
    path('test/reset-connect-check', views.ResetConnectCheck.as_view()),
]