from django.contrib import admin

from apps.products.models import Product, OrderBumpProduct, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity')


class OrderBumpInline(admin.TabularInline):
    model = OrderBumpProduct
    fk_name = 'main_product'
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'product_type', 'price', 'is_active', 'created_at')
    list_filter = ('product_type', 'is_active', 'project')
    search_fields = ('name',)
    inlines = [OrderBumpInline]


@admin.register(OrderBumpProduct)
class OrderBumpProductAdmin(admin.ModelAdmin):
    list_display = ('main_product', 'bump_product', 'headline', 'sort_order')
    list_filter = ('main_product',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact', 'project', 'status', 'total_amount', 'created_at', 'completed_at')
    list_filter = ('status', 'project')
    search_fields = ('contact__email', 'contact__name')
    readonly_fields = ('stripe_session_id', 'stripe_payment_intent_id')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'price', 'quantity')
    list_filter = ('product',)
