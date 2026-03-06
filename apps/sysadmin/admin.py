from django.contrib import admin
from .models import SupportThread, SupportMessage, Inquiry


@admin.register(SupportThread)
class SupportThreadAdmin(admin.ModelAdmin):
    list_display = ('subject', 'project', 'status', 'created_by', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('subject',)


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'is_from_admin', 'read_at', 'created_at')
    list_filter = ('is_from_admin',)


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('subject', 'contact', 'site', 'status', 'created_at', 'replied_at')
    list_filter = ('status',)
    search_fields = ('subject',)
