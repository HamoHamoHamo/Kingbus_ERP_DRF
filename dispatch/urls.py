from django.urls import path
from . import views


urlpatterns = [
    path('monthly/<str:month>', views.MonthlyDispatches.as_view()),
    path('daily/<str:date>', views.DailyDispatches.as_view()),
    path('check', views.DriverCheckView.as_view()),
    path('connect/check', views.ConnectCheckView.as_view()),
    path('regularly', views.RegularlyList.as_view()),
    path('regularly/group', views.RegularlyGroupList.as_view()),
    path('regularly/know', views.RegularlyKnow.as_view()),
    path('checklist/morning/<str:date>', views.MorningChecklistView.as_view()),
    path('checklist/evening/<str:date>', views.EveningChecklistView.as_view()),
    path('drivinghistory', views.DrivingHistoryView.as_view()),
    path('team/list', views.TeamConnectListView.as_view()),
    path('team/<int:id>', views.TeamDriverConnectView.as_view()),
    path('test/reset-connect-check', views.ResetConnectCheck.as_view()),
]