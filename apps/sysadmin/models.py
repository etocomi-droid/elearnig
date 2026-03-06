from django.db import models
from django.conf import settings


class SupportThread(models.Model):
    """サポートスレッド（システム管理者 <-> プロジェクト管理者）"""
    STATUS_CHOICES = [
        ('open', 'オープン'),
        ('pending', '対応待ち'),
        ('closed', 'クローズ'),
    ]
    project = models.ForeignKey(
        'accounts.Project', on_delete=models.CASCADE,
        related_name='support_threads'
    )
    subject = models.CharField('件名', max_length=200)
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='open')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_threads'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'support_threads'
        ordering = ['-updated_at']

    def __str__(self):
        return self.subject


class SupportMessage(models.Model):
    """サポートメッセージ"""
    thread = models.ForeignKey(
        SupportThread, on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='support_messages'
    )
    body = models.TextField('本文')
    is_from_admin = models.BooleanField('システム管理者から', default=False)
    read_at = models.DateTimeField('既読日時', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'support_messages'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.thread.subject} - {self.created_at}'


class MemberSession(models.Model):
    """受講生セッション（同一ID使い回し防止用）"""
    contact = models.ForeignKey(
        'contacts.Contact', on_delete=models.CASCADE,
        related_name='member_sessions'
    )
    site = models.ForeignKey(
        'members.MemberSite', on_delete=models.CASCADE,
        related_name='member_sessions'
    )
    session_key = models.CharField('セッションキー', max_length=255)
    ip_address = models.GenericIPAddressField('IPアドレス', null=True, blank=True)
    user_agent = models.CharField('ユーザーエージェント', max_length=500, blank=True)
    logged_in_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField('有効', default=True)

    class Meta:
        db_table = 'member_sessions'
        ordering = ['-logged_in_at']

    def __str__(self):
        return f'{self.contact.email} - {self.site.name}'


class Inquiry(models.Model):
    """受講生問い合わせ"""
    STATUS_CHOICES = [
        ('open', '未対応'),
        ('replied', '返信済み'),
        ('closed', 'クローズ'),
    ]
    contact = models.ForeignKey(
        'contacts.Contact', on_delete=models.CASCADE,
        related_name='inquiries'
    )
    site = models.ForeignKey(
        'members.MemberSite', on_delete=models.CASCADE,
        related_name='inquiries'
    )
    subject = models.CharField('件名', max_length=200)
    body = models.TextField('内容')
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='open')
    admin_reply = models.TextField('管理者返信', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField('返信日時', null=True, blank=True)

    class Meta:
        db_table = 'inquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} - {self.contact.email}'
