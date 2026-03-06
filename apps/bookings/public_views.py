import calendar
import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.bookings.models import (
    Booking,
    BookingAvailability,
    BookingBlockedDate,
    BookingType,
    CalendarIntegration,
    ZoomIntegration,
)
from apps.bookings.services import GoogleCalendarService, ZoomService
from apps.contacts.models import ActivityLog, Contact, ContactTag

logger = logging.getLogger(__name__)

JST = ZoneInfo('Asia/Tokyo')


def _format_time_display(dt):
    """時刻を 'H:MM' 形式でフォーマット（ゼロパディングなし、クロスプラットフォーム対応）"""
    return f'{dt.hour}:{dt.minute:02d}'


def _format_date_jp(dt):
    """日付を 'YYYY年M月D日' 形式でフォーマット（クロスプラットフォーム対応）"""
    return f'{dt.year}年{dt.month}月{dt.day}日'


@require_GET
def available_dates_api(request, booking_type_id):
    """指定月の予約可能日を返すAPI"""
    try:
        booking_type = BookingType.objects.get(pk=booking_type_id, is_active=True)
    except BookingType.DoesNotExist:
        return JsonResponse({'error': '予約タイプが見つかりません。'}, status=404)

    # クエリパラメータから年月を取得
    try:
        year = int(request.GET.get('year', 0))
        month = int(request.GET.get('month', 0))
        if not (1 <= month <= 12) or year < 2000:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'error': '年月の指定が不正です。'}, status=400)

    today = datetime.now(JST).date()

    # その月の日数を取得
    _, days_in_month = calendar.monthrange(year, month)

    # ブロック日を取得
    blocked = set(
        BookingBlockedDate.objects.filter(
            booking_type=booking_type,
            date__year=year,
            date__month=month,
        ).values_list('date', flat=True)
    )

    # 曜日ごとのアクティブな受付時間を取得
    active_days = set(
        BookingAvailability.objects.filter(
            booking_type=booking_type,
            is_active=True,
        ).values_list('day_of_week', flat=True)
    )

    available_dates = []
    for day in range(1, days_in_month + 1):
        d = date(year, month, day)

        # 過去の日付はスキップ
        if d < today:
            continue

        # ブロック日はスキップ
        if d in blocked:
            continue

        # その曜日に受付時間が存在するか
        if d.weekday() in active_days:
            available_dates.append(d.isoformat())

    return JsonResponse({
        'available_dates': available_dates,
        'booking_type': {
            'name': booking_type.name,
            'duration': booking_type.duration_minutes,
        },
    })


@require_GET
def available_times_api(request, booking_type_id):
    """指定日の予約可能時間枠を返すAPI"""
    try:
        booking_type = BookingType.objects.get(pk=booking_type_id, is_active=True)
    except BookingType.DoesNotExist:
        return JsonResponse({'error': '予約タイプが見つかりません。'}, status=404)

    # クエリパラメータから日付を取得
    date_str = request.GET.get('date', '')
    try:
        selected_date = date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return JsonResponse({'error': '日付の指定が不正です。'}, status=400)

    today = datetime.now(JST).date()
    if selected_date < today:
        return JsonResponse({'date': date_str, 'slots': []})

    # ブロック日チェック
    if BookingBlockedDate.objects.filter(
        booking_type=booking_type, date=selected_date
    ).exists():
        return JsonResponse({'date': date_str, 'slots': []})

    # 曜日の受付時間を取得
    day_of_week = selected_date.weekday()
    availabilities = BookingAvailability.objects.filter(
        booking_type=booking_type,
        day_of_week=day_of_week,
        is_active=True,
    )

    if not availabilities.exists():
        return JsonResponse({'date': date_str, 'slots': []})

    duration = timedelta(minutes=booking_type.duration_minutes)
    buffer_before = timedelta(minutes=booking_type.buffer_before_minutes)
    buffer_after = timedelta(minutes=booking_type.buffer_after_minutes)
    now_jst = datetime.now(JST)

    # 各受付時間ウィンドウからスロットを生成
    all_slots = []
    for avail in availabilities:
        slot_start_dt = datetime.combine(selected_date, avail.start_time, tzinfo=JST)
        window_end_dt = datetime.combine(selected_date, avail.end_time, tzinfo=JST)

        while slot_start_dt + duration <= window_end_dt:
            slot_end_dt = slot_start_dt + duration

            # 今日の場合、過去のスロットはスキップ
            if selected_date == today and slot_start_dt <= now_jst:
                slot_start_dt += duration
                continue

            all_slots.append((slot_start_dt, slot_end_dt))
            slot_start_dt += duration

    if not all_slots:
        return JsonResponse({'date': date_str, 'slots': []})

    # 既存予約を取得（キャンセル済みを除く）
    day_start = datetime.combine(selected_date, time.min, tzinfo=JST)
    day_end = datetime.combine(selected_date, time.max, tzinfo=JST)

    existing_bookings = Booking.objects.filter(
        booking_type=booking_type,
        start_datetime__lt=day_end,
        end_datetime__gt=day_start,
    ).exclude(status='cancelled')

    # 1日の最大予約数チェック
    if booking_type.max_bookings_per_day > 0:
        if existing_bookings.count() >= booking_type.max_bookings_per_day:
            return JsonResponse({'date': date_str, 'slots': []})

    # 既存予約との衝突を除外（バッファを考慮）
    booked_ranges = []
    for b in existing_bookings:
        booked_start = b.start_datetime - buffer_before
        booked_end = b.end_datetime + buffer_after
        booked_ranges.append((booked_start, booked_end))

    # Google Calendar のビジー時間を取得
    try:
        cal_integration = CalendarIntegration.objects.get(
            project=booking_type.project, is_active=True
        )
        gcal_service = GoogleCalendarService(cal_integration)
        busy_times = gcal_service.get_busy_times(day_start, day_end)
        booked_ranges.extend(busy_times)
    except CalendarIntegration.DoesNotExist:
        pass
    except Exception as e:
        logger.warning(f'Google Calendar busy times fetch failed: {e}')

    # 衝突チェックしてフィルタ
    available_slots = []
    for slot_start, slot_end in all_slots:
        # スロット全体（バッファ込み）が既存予約と衝突しないかチェック
        slot_with_buffer_start = slot_start - buffer_before
        slot_with_buffer_end = slot_end + buffer_after
        conflict = False
        for booked_start, booked_end in booked_ranges:
            if slot_with_buffer_start < booked_end and slot_with_buffer_end > booked_start:
                conflict = True
                break
        if not conflict:
            available_slots.append({
                'start': slot_start.strftime('%H:%M'),
                'end': slot_end.strftime('%H:%M'),
                'display': f'{_format_time_display(slot_start)} - {_format_time_display(slot_end)}',
            })

    return JsonResponse({'date': date_str, 'slots': available_slots})


@csrf_exempt
@require_POST
def booking_submit_view(request):
    """予約送信処理"""
    try:
        # リクエストデータを取得
        booking_type_id = request.POST.get('booking_type_id', '')
        selected_date = request.POST.get('selected_date', '')
        selected_time = request.POST.get('selected_time', '')
        email = request.POST.get('email', '').strip()
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        memo = request.POST.get('memo', '').strip()

        # 基本バリデーション
        if not all([booking_type_id, selected_date, selected_time, email, name]):
            return JsonResponse(
                {'success': False, 'error': '必須項目が入力されていません。'},
                status=400,
            )

        # 予約タイプ取得
        try:
            booking_type = BookingType.objects.get(pk=booking_type_id, is_active=True)
        except (BookingType.DoesNotExist, ValueError):
            return JsonResponse(
                {'success': False, 'error': '予約タイプが見つかりません。'},
                status=404,
            )

        # 日時パース
        try:
            book_date = date.fromisoformat(selected_date)
            hour, minute = selected_time.split(':')
            book_time = time(int(hour), int(minute))
        except (ValueError, TypeError):
            return JsonResponse(
                {'success': False, 'error': '日時の指定が不正です。'},
                status=400,
            )

        # 開始・終了日時を構築
        start_datetime = datetime.combine(book_date, book_time, tzinfo=JST)
        end_datetime = start_datetime + timedelta(minutes=booking_type.duration_minutes)

        # 過去の日時チェック
        now_jst = datetime.now(JST)
        if start_datetime <= now_jst:
            return JsonResponse(
                {'success': False, 'error': '過去の日時は予約できません。'},
                status=400,
            )

        # アトミックトランザクション内で予約作成（競合チェック）
        with transaction.atomic():
            # 重複予約チェック
            overlap_exists = Booking.objects.select_for_update().filter(
                booking_type=booking_type,
                start_datetime__lt=end_datetime,
                end_datetime__gt=start_datetime,
            ).exclude(status='cancelled').exists()

            if overlap_exists:
                return JsonResponse(
                    {'success': False, 'error': 'この時間帯は既に予約が入っています。別の時間をお選びください。'},
                    status=409,
                )

            # コンタクト作成・更新
            contact, created = Contact.objects.get_or_create(
                project=booking_type.project,
                email=email,
                defaults={'name': name, 'phone': phone},
            )
            if not created:
                if name:
                    contact.name = name
                if phone:
                    contact.phone = phone
                contact.save()

            # 予約レコード作成
            booking = Booking.objects.create(
                booking_type=booking_type,
                contact=contact,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                status='confirmed',
                guest_memo=memo,
            )

        # --- トランザクション外で外部サービス連携 ---

        # Zoom連携
        if booking_type.location_type == 'zoom':
            try:
                zoom_integration = ZoomIntegration.objects.get(
                    project=booking_type.project, is_active=True
                )
                zoom_service = ZoomService(zoom_integration)
                zoom_result = zoom_service.create_meeting(booking)
                if zoom_result:
                    booking.zoom_meeting_id = zoom_result['id']
                    booking.zoom_join_url = zoom_result['join_url']
                    booking.zoom_start_url = zoom_result['start_url']
                    booking.save(update_fields=[
                        'zoom_meeting_id', 'zoom_join_url', 'zoom_start_url',
                    ])
            except ZoomIntegration.DoesNotExist:
                pass
            except Exception as e:
                logger.error(f'Zoom meeting creation failed for booking {booking.pk}: {e}')

        # Google Calendar連携
        try:
            cal_integration = CalendarIntegration.objects.get(
                project=booking_type.project, is_active=True
            )
            gcal_service = GoogleCalendarService(cal_integration)
            event_id = gcal_service.create_event(booking)
            if event_id:
                booking.google_event_id = event_id
                booking.save(update_fields=['google_event_id'])
        except CalendarIntegration.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f'Google Calendar event creation failed for booking {booking.pk}: {e}')

        # タグ付与
        if booking_type.add_tag:
            try:
                ContactTag.objects.get_or_create(
                    contact=contact,
                    tag=booking_type.add_tag,
                )
            except Exception as e:
                logger.error(f'Tag assignment failed for booking {booking.pk}: {e}')

        # シナリオ開始
        if booking_type.start_scenario:
            try:
                from apps.emails.models import ScenarioSubscription
                ScenarioSubscription.objects.get_or_create(
                    scenario=booking_type.start_scenario,
                    contact=contact,
                )
            except Exception as e:
                logger.error(f'Scenario start failed for booking {booking.pk}: {e}')

        # アクティビティログ記録
        ActivityLog.objects.create(
            contact=contact,
            action='booking',
            detail={
                'booking_id': booking.pk,
                'booking_type': booking_type.name,
                'start_datetime': start_datetime.isoformat(),
                'location_type': booking_type.location_type,
            },
        )

        # 確認メール送信
        if booking_type.confirmation_subject:
            try:
                formatted_date = _format_date_jp(start_datetime)
                formatted_time = f'{_format_time_display(start_datetime)} - {_format_time_display(end_datetime)}'
                body = booking_type.confirmation_body.format(
                    date=formatted_date,
                    time=formatted_time,
                    duration=booking_type.duration_minutes,
                    name=contact.name,
                    booking_type=booking_type.name,
                )
                send_mail(
                    subject=booking_type.confirmation_subject,
                    message=body,
                    from_email=None,  # DEFAULT_FROM_EMAIL を使用
                    recipient_list=[contact.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f'Confirmation email failed for booking {booking.pk}: {e}')

        # 成功レスポンス
        formatted_msg_date = _format_date_jp(start_datetime)
        formatted_msg_time = f'{_format_time_display(start_datetime)} - {_format_time_display(end_datetime)}'

        return JsonResponse({
            'success': True,
            'message': f'{formatted_msg_date} {formatted_msg_time} のご予約を承りました。',
            'booking_id': booking.pk,
        })

    except Exception as e:
        logger.error(f'Booking submit error: {e}', exc_info=True)
        return JsonResponse(
            {'success': False, 'error': '予約処理中にエラーが発生しました。'},
            status=500,
        )


@require_GET
def booking_confirmation_view(request, booking_id):
    """予約確認ページ"""
    booking = get_object_or_404(
        Booking.objects.select_related('booking_type', 'contact'),
        pk=booking_id,
    )

    context = {
        'booking': booking,
        'booking_type': booking.booking_type,
        'contact': booking.contact,
    }

    return render(request, 'bookings/public/booking_confirmation.html', context)
