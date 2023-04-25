from django.urls import path#, include
# from rest_framework import routers
from rest_framework_simplejwt import views as jwt_views
from . import views


urlpatterns = [
    path('login', views.UserLoginView.as_view()),
    # path('drivers/login/', views.DriverLoginView.as_view()),
    # path('companys/login/', views.CompanyLoginView.as_view()),



    # path('token/obtain', jwt_views.TokenObtainPairView.as_view(), name='token_create'),  # override sjwt stock token
    #path('logout', jwt_views.TokenBlacklistView.as_view(), name='logout'),
    path('token/refresh', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    
    # path('userinfo/name', views.userNamereturnView),
]