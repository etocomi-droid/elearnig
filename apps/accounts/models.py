from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Meta:
        db_table = 'users'


class Project(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    name = models.CharField('プロジェクト名', max_length=100)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projects'

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    ROLE_CHOICES = [
        ('admin', '管理者'),
        ('operator', 'オペレーター'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField('役割', max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    can_manage_funnels = models.BooleanField('ファネル管理', default=True)
    can_manage_emails = models.BooleanField('メール配信管理', default=True)
    can_manage_members = models.BooleanField('会員サイト管理', default=True)
    can_manage_contacts = models.BooleanField('コンタクト管理', default=True)
    can_manage_products = models.BooleanField('商品管理', default=True)
    can_manage_bookings = models.BooleanField('予約管理', default=True)

    class Meta:
        db_table = 'project_members'
        unique_together = [('project', 'user')]

    def __str__(self):
        return f'{self.user.username} - {self.project.name} ({self.role})'
