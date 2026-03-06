from django.urls import path

from apps.products import webhooks

app_name = 'products_webhook'

urlpatterns = [
    path('stripe/', webhooks.stripe_webhook_view, name='stripe_webhook'),
]
