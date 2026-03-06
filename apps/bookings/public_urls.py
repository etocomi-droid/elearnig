from django.urls import path

from apps.bookings import public_views

app_name = 'bookings_public'

urlpatterns = [
    path('api/<int:booking_type_id>/dates/', public_views.available_dates_api, name='available_dates'),
    path('api/<int:booking_type_id>/times/', public_views.available_times_api, name='available_times'),
    path('submit/', public_views.booking_submit_view, name='booking_submit'),
    path('confirmation/<int:booking_id>/', public_views.booking_confirmation_view, name='booking_confirmation'),
]
