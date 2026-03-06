from django.contrib import admin
from apps.emails.models import (
    Scenario, ScenarioStep, ScenarioSubscription,
    Campaign, EmailLog,
)


class ScenarioStepInline(admin.TabularInline):
    model = ScenarioStep
    extra = 0
    ordering = ['step_number']


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'project']
    search_fields = ['name']
    inlines = [ScenarioStepInline]


@admin.register(ScenarioStep)
class ScenarioStepAdmin(admin.ModelAdmin):
    list_display = ['scenario', 'step_number', 'subject', 'delay_days', 'delay_hours', 'is_active']
    list_filter = ['is_active', 'scenario__project']
    search_fields = ['subject']
    ordering = ['scenario', 'step_number']


@admin.register(ScenarioSubscription)
class ScenarioSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['scenario', 'contact', 'current_step', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'scenario']
    search_fields = ['contact__email', 'contact__name']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'subject', 'status', 'scheduled_at', 'sent_at', 'created_at']
    list_filter = ['status', 'project']
    search_fields = ['name', 'subject']
    filter_horizontal = ['target_tags']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['contact', 'subject', 'email_type', 'status', 'sent_at', 'opened_at']
    list_filter = ['email_type', 'status']
    search_fields = ['contact__email', 'subject']
    readonly_fields = ['sent_at']
