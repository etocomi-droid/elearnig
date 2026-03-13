from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.http import JsonResponse

from apps.accounts.views import signup_view, custom_logout_view


# TEMP: debug file listing
def _debug_files(request):
    import os
    base = '/var/task'
    templates_dir = os.path.join(base, 'templates')
    result = {
        'cwd': os.getcwd(),
        'base_contents': sorted(os.listdir(base)) if os.path.isdir(base) else 'NOT FOUND',
        'templates_exists': os.path.isdir(templates_dir),
    }
    if os.path.isdir(templates_dir):
        all_files = []
        for root, dirs, files in os.walk(templates_dir):
            for f in files:
                all_files.append(os.path.relpath(os.path.join(root, f), base))
        result['template_files'] = sorted(all_files)
    else:
        result['template_files'] = []
    return JsonResponse(result)


urlpatterns = [
    path('_debug/files/', _debug_files),
    path('django-admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('signup/', signup_view, name='signup'),
    path('', include('apps.accounts.urls')),
    path('contacts/', include('apps.contacts.urls')),
    path('funnels/', include('apps.funnels.urls')),
    path('emails/', include('apps.emails.urls')),
    path('products/', include('apps.products.urls')),
    path('members/', include('apps.members.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('system/', include('apps.sysadmin.urls')),
    path('p/', include('apps.funnels.public_urls')),  # 公開ファネルページ
    path('b/', include('apps.bookings.public_urls')),  # 公開予約ページ
    path('m/', include('apps.members.public_urls')),  # 会員サイト
    path('checkout/', include('apps.products.checkout_urls')),
    path('webhooks/', include('apps.products.webhook_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
