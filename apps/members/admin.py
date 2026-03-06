from django.contrib import admin
from apps.members.models import MemberSite, Course, Lesson, Enrollment, LessonProgress


@admin.register(MemberSite)
class MemberSiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'project', 'is_active', 'created_at']
    list_filter = ['is_active', 'project']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'site', 'slug', 'sort_order', 'is_published', 'created_at']
    list_filter = ['is_published', 'site']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'content_type', 'sort_order', 'is_published', 'is_preview']
    list_filter = ['content_type', 'is_published', 'is_preview', 'course']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['contact', 'course', 'granted_at', 'expires_at']
    list_filter = ['course__site']
    search_fields = ['contact__email', 'contact__name']
    raw_id_fields = ['contact', 'course', 'order']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'lesson', 'is_completed', 'completed_at', 'last_accessed_at']
    list_filter = ['is_completed']
    raw_id_fields = ['enrollment', 'lesson']
