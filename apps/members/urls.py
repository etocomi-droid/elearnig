from django.urls import path
from apps.members.views import (
    SiteListView,
    site_create_view,
    site_edit_view,
    course_create_view,
    course_edit_view,
    course_delete_view,
    lesson_create_view,
    lesson_edit_view,
    lesson_delete_view,
    quiz_setup_view,
    quiz_delete_view,
    question_create_view,
    question_edit_view,
    question_delete_view,
    certificate_edit_view,
    quiz_attempts_view,
)

app_name = 'members'

urlpatterns = [
    path('sites/', SiteListView.as_view(), name='member_site_list'),
    path('sites/create/', site_create_view, name='site_create'),
    path('sites/<int:pk>/edit/', site_edit_view, name='site_edit'),
    path('courses/create/', course_create_view, name='course_create'),
    path('courses/<int:pk>/edit/', course_edit_view, name='course_edit'),
    path('courses/<int:pk>/delete/', course_delete_view, name='course_delete'),
    path('lessons/create/', lesson_create_view, name='lesson_create'),
    path('lessons/<int:pk>/edit/', lesson_edit_view, name='lesson_edit'),
    path('lessons/<int:pk>/delete/', lesson_delete_view, name='lesson_delete'),
    path('lessons/<int:pk>/quiz/setup/', quiz_setup_view, name='quiz_setup'),
    path('lessons/<int:pk>/quiz/delete/', quiz_delete_view, name='quiz_delete'),
    path('quiz/<int:pk>/questions/create/', question_create_view, name='question_create'),
    path('quiz/questions/<int:pk>/edit/', question_edit_view, name='question_edit'),
    path('quiz/questions/<int:pk>/delete/', question_delete_view, name='question_delete'),
    path('courses/<int:pk>/certificate/', certificate_edit_view, name='certificate_edit'),
    path('quiz/<int:pk>/attempts/', quiz_attempts_view, name='quiz_attempts'),
]
