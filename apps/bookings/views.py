from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from apps.accounts.decorators import project_permission_required
from apps.bookings.forms import (
    BookingTypeForm, BookingAvailabilityForm, BookingBlockedDateForm,
    CalendarIntegrationForm, ZoomIntegrationForm,
)
from apps.bookings.models import (
    BookingType, BookingAvailability, BookingBlockedDate,
    Booking, CalendarIntegration, ZoomIntegration,
)


# ---------- 予約タイプ一覧 ----------

@method_decorator(project_permission_required('can_manage_bookings'), name='dispatch')
class BookingTypeListView(LoginRequiredMixin, ListView):
    """予約タイプ一覧"""
    model = BookingType
    template_name = 'bookings/booking_type_list.html'
    context_object_name = 'booking_types'

    def get_queryset(self):
        project = self.request.current_project
        return BookingType.objects.filter(project=project).annotate(
            booking_count=Count('bookings', distinct=True),
        )


# ---------- 予約タイプ作成 ----------

@login_required
@project_permission_required('can_manage_bookings')
def booking_type_create_view(request):
    """予約タイプ作成"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    if request.method == 'POST':
        form = BookingTypeForm(request.POST, current_project=project)
        if form.is_valid():
            booking_type = form.save(commit=False)
            booking_type.project = project
            booking_type.save()
            messages.success(request, f'予約タイプ「{booking_type.name}」を作成しました。')
            return redirect('bookings:booking_type_edit', pk=booking_type.pk)
    else:
        form = BookingTypeForm(current_project=project)

    return render(request, 'bookings/booking_type_edit.html', {
        'form': form,
        'is_new': True,
    })


# ---------- 予約タイプ編集 ----------

@login_required
@project_permission_required('can_manage_bookings')
def booking_type_edit_view(request, pk):
    """予約タイプ編集"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    booking_type = get_object_or_404(BookingType, pk=pk, project=project)

    if request.method == 'POST':
        form = BookingTypeForm(request.POST, instance=booking_type, current_project=project)
        if form.is_valid():
            form.save()
            messages.success(request, '予約タイプを更新しました。')
            return redirect('bookings:booking_type_edit', pk=booking_type.pk)
    else:
        form = BookingTypeForm(instance=booking_type, current_project=project)

    # 曜日別受付時間（0=月〜6=日）
    all_availabilities = booking_type.availabilities.all()
    availabilities = {}
    for day in range(7):
        availabilities[day] = all_availabilities.filter(day_of_week=day)

    # ブロック日
    blocked_dates = booking_type.blocked_dates.all()

    return render(request, 'bookings/booking_type_edit.html', {
        'form': form,
        'booking_type': booking_type,
        'availabilities': availabilities,
        'blocked_dates': blocked_dates,
        'is_new': False,
    })


# ---------- 予約タイプ削除 ----------

@login_required
@project_permission_required('can_manage_bookings')
def booking_type_delete_view(request, pk):
    """予約タイプ削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    booking_type = get_object_or_404(BookingType, pk=pk, project=project)

    if request.method == 'POST':
        name = booking_type.name
        booking_type.delete()
        messages.success(request, f'予約タイプ「{name}」を削除しました。')
        return redirect('bookings:booking_type_list')

    return redirect('bookings:booking_type_edit', pk=booking_type.pk)


# ---------- 受付時間保存 (HTMX) ----------

@login_required
@project_permission_required('can_manage_bookings')
def availability_save_view(request, pk):
    """受付時間を追加"""
    project = getattr(request, 'current_project', None)
    if not project:
        return HttpResponse(status=403)

    booking_type = get_object_or_404(BookingType, pk=pk, project=project)

    if request.method == 'POST':
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if day_of_week and start_time and end_time:
            BookingAvailability.objects.create(
                booking_type=booking_type,
                day_of_week=int(day_of_week),
                start_time=start_time,
                end_time=end_time,
            )

        # 全曜日の受付時間を返す
        all_availabilities = booking_type.availabilities.all()
        availabilities = {}
        for day in range(7):
            availabilities[day] = all_availabilities.filter(day_of_week=day)

        return render(request, 'bookings/partials/availability_form.html', {
            'booking_type': booking_type,
            'availabilities': availabilities,
        })

    return HttpResponse(status=405)


# ---------- 受付時間削除 (HTMX) ----------

@login_required
@project_permission_required('can_manage_bookings')
def availability_delete_view(request, pk):
    """受付時間を削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return HttpResponse(status=403)

    availability = get_object_or_404(
        BookingAvailability, pk=pk, booking_type__project=project
    )
    booking_type = availability.booking_type

    if request.method == 'POST':
        availability.delete()

        all_availabilities = booking_type.availabilities.all()
        availabilities = {}
        for day in range(7):
            availabilities[day] = all_availabilities.filter(day_of_week=day)

        return render(request, 'bookings/partials/availability_form.html', {
            'booking_type': booking_type,
            'availabilities': availabilities,
        })

    return HttpResponse(status=405)


# ---------- ブロック日追加 (HTMX) ----------

@login_required
@project_permission_required('can_manage_bookings')
def blocked_date_add_view(request, pk):
    """ブロック日を追加"""
    project = getattr(request, 'current_project', None)
    if not project:
        return HttpResponse(status=403)

    booking_type = get_object_or_404(BookingType, pk=pk, project=project)

    if request.method == 'POST':
        date = request.POST.get('date')
        reason = request.POST.get('reason', '')

        if date:
            BookingBlockedDate.objects.get_or_create(
                booking_type=booking_type,
                date=date,
                defaults={'reason': reason},
            )

        blocked_dates = booking_type.blocked_dates.all()
        return render(request, 'bookings/partials/blocked_date_list.html', {
            'booking_type': booking_type,
            'blocked_dates': blocked_dates,
        })

    return HttpResponse(status=405)


# ---------- ブロック日削除 (HTMX) ----------

@login_required
@project_permission_required('can_manage_bookings')
def blocked_date_delete_view(request, pk):
    """ブロック日を削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return HttpResponse(status=403)

    blocked_date = get_object_or_404(
        BookingBlockedDate, pk=pk, booking_type__project=project
    )
    booking_type = blocked_date.booking_type

    if request.method == 'POST':
        blocked_date.delete()

        blocked_dates = booking_type.blocked_dates.all()
        return render(request, 'bookings/partials/blocked_date_list.html', {
            'booking_type': booking_type,
            'blocked_dates': blocked_dates,
        })

    return HttpResponse(status=405)


# ---------- 予約一覧 ----------

@method_decorator(project_permission_required('can_manage_bookings'), name='dispatch')
class BookingListView(LoginRequiredMixin, ListView):
    """予約一覧"""
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        project = self.request.current_project
        return Booking.objects.filter(
            booking_type__project=project,
        ).select_related('booking_type', 'contact').order_by('-start_datetime')


# ---------- 予約詳細 ----------

@login_required
@project_permission_required('can_manage_bookings')
def booking_detail_view(request, pk):
    """予約詳細"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    booking = get_object_or_404(
        Booking.objects.select_related('booking_type', 'contact'),
        pk=pk,
        booking_type__project=project,
    )

    return render(request, 'bookings/booking_detail.html', {
        'booking': booking,
    })


# ---------- 予約キャンセル ----------

@login_required
@project_permission_required('can_manage_bookings')
def booking_cancel_view(request, pk):
    """予約キャンセル"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    booking = get_object_or_404(
        Booking, pk=pk, booking_type__project=project,
    )

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.save()
        messages.success(request, '予約をキャンセルしました。')

    return redirect('bookings:booking_detail', pk=booking.pk)


# ---------- 連携設定 ----------

@login_required
@project_permission_required('can_manage_bookings')
def integration_settings_view(request):
    """連携設定（Google Calendar + Zoom）"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    calendar_integration, _ = CalendarIntegration.objects.get_or_create(
        project=project,
    )
    zoom_integration, _ = ZoomIntegration.objects.get_or_create(
        project=project,
    )

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'calendar':
            calendar_form = CalendarIntegrationForm(request.POST, instance=calendar_integration)
            zoom_form = ZoomIntegrationForm(instance=zoom_integration)
            if calendar_form.is_valid():
                calendar_form.save()
                messages.success(request, 'Googleカレンダー連携設定を更新しました。')
                return redirect('bookings:integration_settings')
        elif form_type == 'zoom':
            calendar_form = CalendarIntegrationForm(instance=calendar_integration)
            zoom_form = ZoomIntegrationForm(request.POST, instance=zoom_integration)
            if zoom_form.is_valid():
                zoom_form.save()
                messages.success(request, 'Zoom連携設定を更新しました。')
                return redirect('bookings:integration_settings')
        else:
            calendar_form = CalendarIntegrationForm(instance=calendar_integration)
            zoom_form = ZoomIntegrationForm(instance=zoom_integration)
    else:
        calendar_form = CalendarIntegrationForm(instance=calendar_integration)
        zoom_form = ZoomIntegrationForm(instance=zoom_integration)

    return render(request, 'bookings/integration_settings.html', {
        'calendar_form': calendar_form,
        'zoom_form': zoom_form,
    })
