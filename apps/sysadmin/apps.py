from django.apps import AppConfig


class SysadminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sysadmin'
    verbose_name = 'システム管理'
