from django.contrib import admin
from apps.contacts.models import Contact, Tag, ContactTag, ActivityLog


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'project', 'phone', 'created_at')
    list_filter = ('project', 'created_at')
    search_fields = ('name', 'email', 'phone')
    ordering = ('-created_at',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'color')
    list_filter = ('project',)
    search_fields = ('name',)


@admin.register(ContactTag)
class ContactTagAdmin(admin.ModelAdmin):
    list_display = ('contact', 'tag', 'created_at')
    list_filter = ('tag',)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('contact', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('contact__name', 'contact__email')
    ordering = ('-created_at',)
