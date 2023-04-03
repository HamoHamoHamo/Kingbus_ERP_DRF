from django.urls import path
from . import views


urlpatterns = [
    path('monthly/<str:month>', views.MonthlyDispatches.as_view()),
    path('daily/<str:date>', views.DailyDispatches.as_view()),
    path('test/<str:date>', views.test.as_view()),
]