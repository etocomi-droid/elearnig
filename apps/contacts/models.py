from django.db import models


class Contact(models.Model):
    project = models.ForeignKey('accounts.Project', on_delete=models.CASCADE, related_name='contacts')
    email = models.EmailField('メールアドレス')
    name = models.CharField('名前', max_length=100, blank=True)
    phone = models.CharField('電話番号', max_length=20, blank=True)
    memo = models.TextField('メモ', blank=True)
    password_hash = models.CharField('パスワード', max_length=128, blank=True)  # 会員サイトログイン用
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contacts'
        unique_together = [('project', 'email')]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name or self.email}'


class Tag(models.Model):
    project = models.ForeignKey('accounts.Project', on_delete=models.CASCADE, related_name='tags')
    name = models.CharField('タグ名', max_length=50)
    color = models.CharField('カラー', max_length=7, default='#3B82F6')

    class Meta:
        db_table = 'tags'
        unique_together = [('project', 'name')]

    def __str__(self):
        return self.name


class ContactTag(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='contact_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='contact_tags')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contact_tags'
        unique_together = [('contact', 'tag')]


class ActivityLog(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField('アクション', max_length=50)
    detail = models.JSONField('詳細', default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
