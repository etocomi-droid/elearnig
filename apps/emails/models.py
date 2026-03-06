from django.db import models


class Scenario(models.Model):
    project = models.ForeignKey('accounts.Project', on_delete=models.CASCADE, related_name='scenarios')
    name = models.CharField('シナリオ名', max_length=200)
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scenarios'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ScenarioStep(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='steps')
    step_number = models.IntegerField('ステップ番号')
    delay_days = models.IntegerField('遅延日数', default=0)
    delay_hours = models.IntegerField('遅延時間', default=0)
    subject = models.CharField('件名', max_length=200)
    body_html = models.TextField('本文(HTML)')
    body_text = models.TextField('本文(テキスト)', blank=True)
    is_active = models.BooleanField('有効', default=True)

    class Meta:
        db_table = 'scenario_steps'
        ordering = ['step_number']

    def __str__(self):
        return f'{self.scenario.name} - Step {self.step_number}'


class ScenarioSubscription(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='subscriptions')
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='scenario_subscriptions')
    subscribed_at = models.DateTimeField(auto_now_add=True)
    current_step = models.IntegerField('現在のステップ', default=0)
    is_active = models.BooleanField('有効', default=True)

    class Meta:
        db_table = 'scenario_subscriptions'
        unique_together = [('scenario', 'contact')]

    def __str__(self):
        return f'{self.contact} -> {self.scenario.name} (Step {self.current_step})'


class Campaign(models.Model):
    STATUS_CHOICES = [
        ('draft', '下書き'),
        ('scheduled', '予約済み'),
        ('sending', '送信中'),
        ('sent', '送信済み'),
    ]
    project = models.ForeignKey('accounts.Project', on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField('キャンペーン名', max_length=200)
    subject = models.CharField('件名', max_length=200)
    body_html = models.TextField('本文(HTML)')
    body_text = models.TextField('本文(テキスト)', blank=True)
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField('配信予定日時', null=True, blank=True)
    sent_at = models.DateTimeField('配信日時', null=True, blank=True)
    target_tags = models.ManyToManyField('contacts.Tag', blank=True, verbose_name='ターゲットタグ')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class EmailLog(models.Model):
    EMAIL_TYPE_CHOICES = [
        ('scenario', 'シナリオ'),
        ('campaign', '一斉配信'),
    ]
    STATUS_CHOICES = [
        ('sent', '送信済'),
        ('failed', '失敗'),
        ('opened', '開封'),
        ('clicked', 'クリック'),
    ]
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='email_logs')
    subject = models.CharField('件名', max_length=200)
    email_type = models.CharField('種別', max_length=20, choices=EMAIL_TYPE_CHOICES)
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    scenario_step = models.ForeignKey(ScenarioStep, on_delete=models.SET_NULL, null=True, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'email_logs'
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.contact} - {self.subject} ({self.status})'
