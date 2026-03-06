from django.contrib import admin

from apps.bookings.models import (
    BookingType, BookingAvailability, BookingBlockedDate,
    Booking, CalendarIntegration, ZoomIntegration,
)

admin.site.register(BookingType)
admin.site.register(Booking)
