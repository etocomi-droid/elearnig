from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('signup/', views.signup_view, name='signup'),
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.project_create_view, name='project_create'),
    path('projects/<slug:slug>/switch/', views.project_switch_view, name='project_switch'),
    path('manual/', views.ManualIndexView.as_view(), name='manual_index'),
    path('manual/<int:chapter_num>/', views.ManualChapterView.as_view(), name='manual_chapter'),
    path('settings/operators/', views.OperatorListView.as_view(), name='operator_list'),
    path('settings/operators/invite/', views.operator_invite_view, name='operator_invite'),
    path('settings/operators/<int:pk>/edit/', views.operator_edit_view, name='operator_edit'),
    path('settings/operators/<int:pk>/delete/', views.operator_delete_view, name='operator_delete'),
    # サポート
    path('support/', views.ProjectSupportListView.as_view(), name='support_list'),
    path('support/create/', views.project_support_create_view, name='support_create'),
    path('support/<int:pk>/', views.project_support_detail_view, name='support_detail'),
    path('support/<int:pk>/reply/', views.project_support_reply_view, name='support_reply'),
    # 問い合わせ管理
    path('inquiries/', views.ProjectInquiryListView.as_view(), name='inquiry_list'),
    path('inquiries/<int:pk>/', views.project_inquiry_detail_view, name='inquiry_detail'),
    path('inquiries/<int:pk>/reply/', views.project_inquiry_reply_view, name='inquiry_reply'),
]
