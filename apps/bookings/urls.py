from django.urls import path

from apps.bookings.views import (
    BookingTypeListView,
    booking_type_create_view,
    booking_type_edit_view,
    booking_type_delete_view,
    availability_save_view,
    availability_delete_view,
    blocked_date_add_view,
    blocked_date_delete_view,
    BookingListView,
    booking_detail_view,
    booking_cancel_view,
    integration_settings_view,
)

app_name = 'bookings'

urlpatterns = [
    path('', BookingTypeListView.as_view(), name='booking_type_list'),
    path('types/create/', booking_type_create_view, name='booking_type_create'),
    path('types/<int:pk>/edit/', booking_type_edit_view, name='booking_type_edit'),
    path('types/<int:pk>/delete/', booking_type_delete_view, name='booking_type_delete'),
    path('types/<int:pk>/availability/', availability_save_view, name='availability_save'),
    path('availability/<int:pk>/delete/', availability_delete_view, name='availability_delete'),
    path('types/<int:pk>/blocked-dates/add/', blocked_date_add_view, name='blocked_date_add'),
    path('blocked-dates/<int:pk>/delete/', blocked_date_delete_view, name='blocked_date_delete'),
    path('list/', BookingListView.as_view(), name='booking_list'),
    path('<int:pk>/', booking_detail_view, name='booking_detail'),
    path('<int:pk>/cancel/', booking_cancel_view, name='booking_cancel'),
    path('integrations/', integration_settings_view, name='integration_settings'),
]
