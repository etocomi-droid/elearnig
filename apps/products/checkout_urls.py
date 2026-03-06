from django.urls import path

from apps.products import checkout_views

app_name = 'products_checkout'

urlpatterns = [
    path('<int:product_id>/', checkout_views.checkout_create_view, name='checkout_create'),
    path('success/', checkout_views.checkout_success_view, name='checkout_success'),
    path('cancel/', checkout_views.checkout_cancel_view, name='checkout_cancel'),
]
