from django.db import models


class Product(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('one_time', '単品'),
        ('subscription', 'サブスクリプション'),
    ]
    BILLING_INTERVAL_CHOICES = [
        ('month', '月額'),
        ('year', '年額'),
    ]
    project = models.ForeignKey('accounts.Project', on_delete=models.CASCADE, related_name='products')
    name = models.CharField('商品名', max_length=200)
    description = models.TextField('説明', blank=True)
    product_type = models.CharField('商品タイプ', max_length=20, choices=PRODUCT_TYPE_CHOICES, default='one_time')
    price = models.IntegerField('価格(円)')
    stripe_product_id = models.CharField(max_length=100, blank=True)
    stripe_price_id = models.CharField(max_length=100, blank=True)
    # 購入後アクション
    grant_course = models.ForeignKey(
        'members.Course', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='アクセス権付与コース',
    )
    add_tag = models.ForeignKey(
        'contacts.Tag', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='タグ付与',
    )
    start_scenario = models.ForeignKey(
        'emails.Scenario', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='シナリオ開始',
    )
    billing_interval = models.CharField(
        '課金間隔', max_length=10, choices=BILLING_INTERVAL_CHOICES, blank=True,
    )
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class OrderBumpProduct(models.Model):
    main_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_bumps')
    bump_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bumped_by')
    headline = models.CharField('見出し', max_length=200)
    description = models.TextField('説明')
    sort_order = models.IntegerField('表示順', default=0)

    class Meta:
        db_table = 'order_bump_products'

    def __str__(self):
        return f'{self.main_product.name} + {self.bump_product.name}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '処理中'),
        ('completed', '完了'),
        ('refunded', '返金済'),
        ('cancelled', 'キャンセル'),
    ]
    project = models.ForeignKey('accounts.Project', on_delete=models.CASCADE, related_name='orders')
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='orders')
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.IntegerField('合計金額')
    stripe_session_id = models.CharField(max_length=200, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'注文 #{self.id} - {self.contact}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.IntegerField('価格')
    quantity = models.IntegerField('数量', default=1)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
