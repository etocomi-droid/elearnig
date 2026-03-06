from django.db import models


class BookingType(models.Model):
    """予約タイプ定義"""

    LOCATION_CHOICES = [
        ('zoom', 'Zoom'),
        ('google_meet', 'Google Meet'),
        ('phone', '電話'),
        ('in_person', '対面'),
    ]

    project = models.ForeignKey(
        'accounts.Project', on_delete=models.CASCADE, related_name='booking_types'
    )
    name = models.CharField('予約タイプ名', max_length=200)
    slug = models.SlugField('スラッグ')
    description = models.TextField('説明', blank=True)
    duration_minutes = models.IntegerField('所要時間(分)', default=30)
    location_type = models.CharField(
        '場所タイプ', max_length=20, choices=LOCATION_CHOICES, default='zoom'
    )
    location_detail = models.CharField('場所詳細', max_length=500, blank=True)
    buffer_before_minutes = models.IntegerField('前バッファ(分)', default=0)
    buffer_after_minutes = models.IntegerField('後バッファ(分)', default=10)
    max_bookings_per_day = models.IntegerField(
        '1日の最大予約数', default=0, help_text='0=無制限'
    )
    add_tag = models.ForeignKey(
        'contacts.Tag', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='タグ付与'
    )
    start_scenario = models.ForeignKey(
        'emails.Scenario', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='シナリオ開始'
    )
    confirmation_subject = models.CharField(
        '確認メール件名', max_length=200, blank=True, default='ご予約が確定しました'
    )
    confirmation_body = models.TextField(
        '確認メール本文', blank=True,
        default='ご予約ありがとうございます。\n\n日時: {date} {time}\n所要時間: {duration}分'
    )
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_types'
        unique_together = [('project', 'slug')]
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class BookingAvailability(models.Model):
    """曜日別受付時間"""

    DAY_OF_WEEK_CHOICES = [
        (0, '月曜日'),
        (1, '火曜日'),
        (2, '水曜日'),
        (3, '木曜日'),
        (4, '金曜日'),
        (5, '土曜日'),
        (6, '日曜日'),
    ]

    booking_type = models.ForeignKey(
        BookingType, on_delete=models.CASCADE, related_name='availabilities'
    )
    day_of_week = models.IntegerField('曜日', choices=DAY_OF_WEEK_CHOICES)
    start_time = models.TimeField('開始時間')
    end_time = models.TimeField('終了時間')
    is_active = models.BooleanField('有効', default=True)

    class Meta:
        db_table = 'booking_availabilities'
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f'{self.get_day_of_week_display()} {self.start_time}-{self.end_time}'


class BookingBlockedDate(models.Model):
    """ブロック日"""

    booking_type = models.ForeignKey(
        BookingType, on_delete=models.CASCADE, related_name='blocked_dates'
    )
    date = models.DateField('ブロック日')
    reason = models.CharField('理由', max_length=200, blank=True)

    class Meta:
        db_table = 'booking_blocked_dates'
        unique_together = [('booking_type', 'date')]
        ordering = ['date']

    def __str__(self):
        return f'{self.date} ({self.reason})'


class Booking(models.Model):
    """予約レコード"""

    STATUS_CHOICES = [
        ('confirmed', '確定'),
        ('cancelled', 'キャンセル'),
        ('completed', '完了'),
        ('no_show', 'ノーショー'),
    ]

    booking_type = models.ForeignKey(
        BookingType, on_delete=models.CASCADE, related_name='bookings'
    )
    contact = models.ForeignKey(
        'contacts.Contact', on_delete=models.CASCADE, related_name='bookings'
    )
    start_datetime = models.DateTimeField('開始日時')
    end_datetime = models.DateTimeField('終了日時')
    status = models.CharField(
        'ステータス', max_length=20, choices=STATUS_CHOICES, default='confirmed'
    )
    google_event_id = models.CharField(
        'GoogleカレンダーイベントID', max_length=200, blank=True
    )
    zoom_meeting_id = models.CharField('ZoomミーティングID', max_length=200, blank=True)
    zoom_join_url = models.CharField('Zoom参加URL', max_length=500, blank=True)
    zoom_start_url = models.CharField('ZoomホストURL', max_length=500, blank=True)
    guest_memo = models.TextField('ゲストメモ', blank=True)
    admin_memo = models.TextField('管理者メモ', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField('キャンセル日時', null=True, blank=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-start_datetime']

    def __str__(self):
        return f'{self.booking_type.name} - {self.contact} ({self.start_datetime})'


class CalendarIntegration(models.Model):
    """Google Calendar連携設定"""

    project = models.OneToOneField(
        'accounts.Project', on_delete=models.CASCADE, related_name='calendar_integration'
    )
    credentials_json = models.TextField('認証情報(JSON)', blank=True)
    calendar_id = models.CharField('カレンダーID', max_length=200, default='primary')
    is_active = models.BooleanField('有効', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calendar_integrations'

    def __str__(self):
        return f'Calendar: {self.project}'


class ZoomIntegration(models.Model):
    """Zoom連携設定"""

    project = models.OneToOneField(
        'accounts.Project', on_delete=models.CASCADE, related_name='zoom_integration'
    )
    account_id = models.CharField('アカウントID', max_length=200, blank=True)
    client_id = models.CharField('クライアントID', max_length=200, blank=True)
    client_secret = models.CharField('クライアントシークレット', max_length=200, blank=True)
    is_active = models.BooleanField('有効', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'zoom_integrations'

    def __str__(self):
        return f'Zoom: {self.project}'
