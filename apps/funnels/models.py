from django.db import models


class Funnel(models.Model):
    project = models.ForeignKey(
        'accounts.Project', on_delete=models.CASCADE, related_name='funnels'
    )
    name = models.CharField('ファネル名', max_length=200)
    slug = models.SlugField('スラッグ')
    is_published = models.BooleanField('公開', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'funnels'
        unique_together = [('project', 'slug')]

    def __str__(self):
        return self.name


class FunnelPage(models.Model):
    PAGE_TYPE_CHOICES = [
        ('lp', 'ランディングページ'),
        ('thanks', 'サンクスページ'),
        ('sales', 'セールスページ'),
        ('form', 'フォームページ'),
        ('upsell', 'アップセルページ'),
    ]
    funnel = models.ForeignKey(
        Funnel, on_delete=models.CASCADE, related_name='pages'
    )
    title = models.CharField('ページタイトル', max_length=200)
    slug = models.SlugField('スラッグ')
    page_type = models.CharField(
        'ページタイプ', max_length=20, choices=PAGE_TYPE_CHOICES, default='lp'
    )
    sort_order = models.IntegerField('表示順', default=0)
    meta_title = models.CharField('メタタイトル', max_length=200, blank=True)
    meta_description = models.TextField('メタディスクリプション', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'funnel_pages'
        ordering = ['sort_order']

    def __str__(self):
        return self.title


class PageSection(models.Model):
    SECTION_TYPE_CHOICES = [
        ('hero', 'ヒーローセクション'),
        ('text', 'テキスト'),
        ('image', '画像'),
        ('video', '動画埋め込み'),
        ('button', 'CTAボタン'),
        ('form', 'フォーム'),
        ('countdown', 'カウントダウン'),
        ('testimonial', 'お客様の声'),
        ('faq', 'FAQ'),
        ('schedule', 'スケジュール予約'),
        ('meeting', 'ミーティング予約'),
        ('separator', '区切り線'),
    ]
    page = models.ForeignKey(
        FunnelPage, on_delete=models.CASCADE, related_name='sections'
    )
    section_type = models.CharField(
        'セクションタイプ', max_length=20, choices=SECTION_TYPE_CHOICES
    )
    content = models.JSONField('コンテンツ', default=dict)
    sort_order = models.IntegerField('表示順', default=0)
    is_visible = models.BooleanField('表示', default=True)

    class Meta:
        db_table = 'page_sections'
        ordering = ['sort_order']

    def __str__(self):
        return f'{self.get_section_type_display()} (#{self.sort_order})'
