from django.urls import path

from rest_framework_simplejwt import views as jwt_views
from . import views


urlpatterns = [
    path('login', views.UserLoginView.as_view()),
    # path('drivers/login/', views.DriverLoginView.as_view()),
    # path('companys/login/', views.CompanyLoginView.as_view()),
    path('notification', views.Notification.as_view()),
    path('maintenance', views.MaintenanceView.as_view()),
    path('member/list', views.MemberListView.as_view()),
    path('member', views.LoginMemberView.as_view()),
    # path('token/obtain', jwt_views.TokenObtainPairView.as_view(), name='token_create'),  # override sjwt stock token
    #path('logout', jwt_views.TokenBlacklistView.as_view(), name='logout'),
    path('token/refresh', views.TokenRefreshView.as_view(), name='token_refresh'),
    
    # path('userinfo/name', views.userNamereturnView),
]