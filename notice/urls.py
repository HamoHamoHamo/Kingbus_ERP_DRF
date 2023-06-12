from django.urls import path
from . import views

urlpatterns = [
    path('', views.NoticeListView.as_view()),
    path('/<int:id>', views.NoticeDetailView.as_view()),
    path('/comment', views.CommentView.as_view()),
]