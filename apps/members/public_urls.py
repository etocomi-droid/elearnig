from django.urls import path
from apps.members.public_views import (
    member_login_view,
    member_logout_view,
    site_home_view,
    course_detail_view,
    lesson_view,
    lesson_complete_view,
    quiz_start_view,
    quiz_submit_view,
    quiz_result_view,
    certificate_view,
    member_profile_view,
    member_password_change_view,
    member_inquiry_view,
    member_inquiry_history_view,
    member_manual_view,
)

app_name = 'members_public'

urlpatterns = [
    path('<slug:site_slug>/', site_home_view, name='member_home'),
    path('<slug:site_slug>/login/', member_login_view, name='member_login'),
    path('<slug:site_slug>/logout/', member_logout_view, name='member_logout'),
    path('<slug:site_slug>/course/<slug:course_slug>/', course_detail_view, name='member_course'),
    path('<slug:site_slug>/lesson/<slug:lesson_slug>/', lesson_view, name='member_lesson'),
    path('<slug:site_slug>/lesson/<slug:lesson_slug>/complete/', lesson_complete_view, name='lesson_complete'),
    path('<slug:site_slug>/quiz/<slug:lesson_slug>/start/', quiz_start_view, name='quiz_start'),
    path('<slug:site_slug>/quiz/<slug:lesson_slug>/submit/', quiz_submit_view, name='quiz_submit'),
    path('<slug:site_slug>/quiz/<slug:lesson_slug>/result/<int:attempt_id>/', quiz_result_view, name='quiz_result'),
    path('<slug:site_slug>/certificate/<str:cert_number>/', certificate_view, name='certificate_view'),
    path('<slug:site_slug>/profile/', member_profile_view, name='member_profile'),
    path('<slug:site_slug>/password/', member_password_change_view, name='member_password'),
    path('<slug:site_slug>/inquiry/', member_inquiry_view, name='member_inquiry'),
    path('<slug:site_slug>/inquiry/history/', member_inquiry_history_view, name='member_inquiry_history'),
    path('<slug:site_slug>/manual/', member_manual_view, name='member_manual'),
]
