from django.contrib import admin

from apps.funnels.models import Funnel, FunnelPage, PageSection


class FunnelPageInline(admin.TabularInline):
    model = FunnelPage
    extra = 0
    fields = ['title', 'slug', 'page_type', 'sort_order']


class PageSectionInline(admin.TabularInline):
    model = PageSection
    extra = 0
    fields = ['section_type', 'sort_order', 'is_visible']


@admin.register(Funnel)
class FunnelAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'slug', 'is_published', 'created_at']
    list_filter = ['is_published', 'project']
    search_fields = ['name', 'slug']
    inlines = [FunnelPageInline]


@admin.register(FunnelPage)
class FunnelPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'funnel', 'slug', 'page_type', 'sort_order']
    list_filter = ['page_type', 'funnel']
    search_fields = ['title', 'slug']
    inlines = [PageSectionInline]


@admin.register(PageSection)
class PageSectionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'page', 'section_type', 'sort_order', 'is_visible']
    list_filter = ['section_type', 'is_visible']
