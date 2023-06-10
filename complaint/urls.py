from django.urls import path
from . import views

urlpatterns = [
    path('consulting', views.ConsultingView.as_view()),
    path('inspection', views.InspectionView.as_view()),
]