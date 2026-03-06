from django.urls import path
from . import views

app_name = 'sysadmin'

urlpatterns = [
    path('login/', views.sysadmin_login_view, name='login'),
    path('', views.sysadmin_dashboard_view, name='dashboard'),
    path('projects/', views.SysadminProjectListView.as_view(), name='project_list'),
    path('projects/<int:pk>/', views.sysadmin_project_detail_view, name='project_detail'),
    path('projects/<int:pk>/switch/', views.sysadmin_switch_to_project_view, name='project_switch'),
    path('users/', views.SysadminUserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.sysadmin_user_detail_view, name='user_detail'),
    path('users/<int:pk>/toggle/', views.sysadmin_user_toggle_view, name='user_toggle'),
    path('support/', views.SysadminSupportListView.as_view(), name='support_list'),
    path('support/<int:pk>/', views.sysadmin_support_detail_view, name='support_detail'),
    path('support/<int:pk>/reply/', views.sysadmin_support_reply_view, name='support_reply'),
    path('inquiries/', views.SysadminInquiryListView.as_view(), name='inquiry_list'),
    path('inquiries/<int:pk>/', views.sysadmin_inquiry_detail_view, name='inquiry_detail'),
    path('inquiries/<int:pk>/reply/', views.sysadmin_inquiry_reply_view, name='inquiry_reply'),
    path('manual/', views.sysadmin_manual_index_view, name='manual_index'),
    path('manual/<int:chapter_num>/', views.sysadmin_manual_chapter_view, name='manual_chapter'),
]
