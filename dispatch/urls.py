from django.urls import path
from . import views


urlpatterns = [
    path('monthly/<str:month>', views.MonthlyDispatches.as_view()),
    path('daily/list/<str:date>', views.DailyListDispatches.as_view()), # 일일배차리스트
    path('daily/detail', views.DispatchDetailView.as_view()), # 상세배차리스트
    path('daily/detail/location-history', views.LocationHistory.as_view()),
    path('daily/routine/get-off-work', views.DailyGetOffWorkView.as_view()),
    path('daily/routine/<str:date>', views.DailyRoutineView.as_view()),
    path('check', views.DriverCheckView.as_view()),
    path('check2', views.DriverCheckView2.as_view()),
    path('connect/check', views.ConnectCheckView.as_view()),
    path('station/check', views.StationCheckView.as_view()),
    path('regularly', views.RegularlyList.as_view()),
    path('regularly/group', views.RegularlyGroupList.as_view()),
    path('regularly/know', views.RegularlyKnow.as_view()),
    path('checklist/morning/<str:date>', views.MorningChecklistView.as_view()),
    path('checklist/evening/<str:date>', views.EveningChecklistView.as_view()),
    path('drivinghistory', views.DrivingHistoryView.as_view()),
    path('driving-history', views.NewDrivingHistoryView.as_view()),
    path('team/list', views.TeamConnectListView.as_view()),
    path('team/<int:id>', views.TeamDriverConnectView.as_view()),
    path('test/reset-connect-check', views.ResetConnectCheck.as_view()),

    # rpa-p
    path('estimate', views.EstimateView.as_view()),
    path('estimate/reservation/confirm', views.EstimateReservationConfirmView.as_view()),
    path('estimate/contract', views.EstimateContract.as_view()),
    path('tour/contract', views.TourContract.as_view()),
    path('tour', views.TourView.as_view()),
    path('send/code', views.send_code), # 전화번호 인증 코드 전송
    path('verify/code', views.verify_code, name='verify_code'), # 전화번호 인증 코드 확인
]