from django.urls import path
from . import views

urlpatterns = [
    path('', views.NoticeListView.as_view()),
    path('/<int:id>', views.NoticeDetailView.as_view()),
    path('/comment', views.CommentView.as_view()),
    path('/read', views.NoticeIsReadView.as_view()),

    path('/rule/approval/print', views.approval_rule_print, name='approval_rule_print'),
    path('/rule/rollcall/print', views.roll_call_rule_print, name='roll_call_rule_print'),
    path('/rule/driver/print', views.driver_rule_print, name='driver_rule_print'),
    path('/rule/manager/print', views.manager_rule_print, name='manager_rule_print'),
    path('/rule/fieldmanager/print', views.field_manager_rule_print, name='field_manager_rule_print'),
    path('/rule/personnelcommittee/print', views.personnel_committee_rule_print, name='personnel_committee_rule_print'),
    
]