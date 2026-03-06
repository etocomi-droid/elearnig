from django.urls import path

from apps.funnels.public_views import public_page_view, form_submit_view

app_name = 'funnels_public'

urlpatterns = [
    path('form-submit/', form_submit_view, name='form_submit'),
    path('<slug:funnel_slug>/<slug:page_slug>/', public_page_view, name='public_page'),
]
