from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Count, Sum, Q

from apps.accounts.models import User, Project, ProjectMember
from apps.contacts.models import Contact
from apps.products.models import Order
from apps.funnels.models import Funnel
from apps.members.models import MemberSite, Course
from apps.sysadmin.models import SupportThread, SupportMessage, Inquiry


def superuser_required(view_func):
    @wraps(view_func)
    @login_required(login_url='/system/login/')
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/system/login/')
        return view_func(request, *args, **kwargs)
    return wrapper


class SuperuserRequiredMixin:
    @method_decorator(superuser_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


# ── Login ──────────────────────────────────────────────

def sysadmin_login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('/system/')
        else:
            error = 'ユーザー名またはパスワードが正しくありません。'
    return render(request, 'sysadmin/login.html', {'error': error})


# ── Dashboard ──────────────────────────────────────────

@superuser_required
def sysadmin_dashboard_view(request):
    total_projects = Project.objects.count()
    total_users = User.objects.filter(is_superuser=False).count()
    total_contacts = Contact.objects.count()

    order_stats = Order.objects.filter(status='completed').aggregate(
        total_orders=Count('id'),
        total_revenue=Sum('total_amount'),
    )
    total_orders = order_stats['total_orders'] or 0
    total_revenue = order_stats['total_revenue'] or 0

    recent_threads = SupportThread.objects.select_related('project', 'created_by')[:5]
    recent_inquiries = Inquiry.objects.select_related('contact', 'site')[:5]

    context = {
        'total_projects': total_projects,
        'total_users': total_users,
        'total_contacts': total_contacts,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_threads': recent_threads,
        'recent_inquiries': recent_inquiries,
    }
    return render(request, 'sysadmin/dashboard.html', context)


# ── Projects ───────────────────────────────────────────

class SysadminProjectListView(SuperuserRequiredMixin, ListView):
    model = Project
    template_name = 'sysadmin/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20

    def get_queryset(self):
        qs = Project.objects.select_related('owner').annotate(
            member_count=Count('members', distinct=True),
            contact_count=Count('contacts', distinct=True),
        ).order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


@superuser_required
def sysadmin_project_detail_view(request, pk):
    project = get_object_or_404(Project.objects.select_related('owner'), pk=pk)
    members = ProjectMember.objects.filter(project=project).select_related('user')
    contact_count = Contact.objects.filter(project=project).count()
    funnel_count = Funnel.objects.filter(project=project).count()
    course_count = Course.objects.filter(site__project=project).count()

    order_stats = Order.objects.filter(project=project, status='completed').aggregate(
        order_count=Count('id'),
        revenue=Sum('total_amount'),
    )

    context = {
        'project': project,
        'members': members,
        'contact_count': contact_count,
        'funnel_count': funnel_count,
        'course_count': course_count,
        'order_count': order_stats['order_count'] or 0,
        'revenue': order_stats['revenue'] or 0,
    }
    return render(request, 'sysadmin/project_detail.html', context)


@superuser_required
def sysadmin_switch_to_project_view(request, pk):
    if request.method != 'POST':
        return redirect('sysadmin:project_list')
    project = get_object_or_404(Project, pk=pk)
    request.session['current_project_id'] = project.pk
    return redirect('/dashboard/')


# ── Users ──────────────────────────────────────────────

class SysadminUserListView(SuperuserRequiredMixin, ListView):
    model = User
    template_name = 'sysadmin/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.filter(is_superuser=False).annotate(
            project_count=Count('owned_projects', distinct=True),
        ).order_by('-date_joined')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


@superuser_required
def sysadmin_user_detail_view(request, pk):
    target_user = get_object_or_404(User, pk=pk, is_superuser=False)
    owned_projects = Project.objects.filter(owner=target_user)
    member_projects = ProjectMember.objects.filter(user=target_user).select_related('project')

    context = {
        'target_user': target_user,
        'owned_projects': owned_projects,
        'member_projects': member_projects,
    }
    return render(request, 'sysadmin/user_detail.html', context)


@superuser_required
def sysadmin_user_toggle_view(request, pk):
    if request.method != 'POST':
        return redirect('sysadmin:user_list')
    target_user = get_object_or_404(User, pk=pk, is_superuser=False)
    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])
    return redirect('sysadmin:user_detail', pk=pk)


# ── Support ────────────────────────────────────────────

class SysadminSupportListView(SuperuserRequiredMixin, ListView):
    model = SupportThread
    template_name = 'sysadmin/support_list.html'
    context_object_name = 'threads'
    paginate_by = 20

    def get_queryset(self):
        qs = SupportThread.objects.select_related('project', 'created_by').annotate(
            message_count=Count('messages'),
        )
        status = self.request.GET.get('status', '').strip()
        if status in ('open', 'pending', 'closed'):
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_status'] = self.request.GET.get('status', '')
        return ctx


@superuser_required
def sysadmin_support_detail_view(request, pk):
    thread = get_object_or_404(
        SupportThread.objects.select_related('project', 'created_by'), pk=pk
    )
    messages = thread.messages.select_related('sender').all()
    context = {
        'thread': thread,
        'messages': messages,
    }
    return render(request, 'sysadmin/support_detail.html', context)


@superuser_required
def sysadmin_support_reply_view(request, pk):
    if request.method != 'POST':
        return redirect('sysadmin:support_detail', pk=pk)
    thread = get_object_or_404(SupportThread, pk=pk)
    body = request.POST.get('body', '').strip()
    if body:
        SupportMessage.objects.create(
            thread=thread,
            sender=request.user,
            body=body,
            is_from_admin=True,
        )
        thread.status = 'pending'
        thread.save(update_fields=['status', 'updated_at'])

    # If HTMX request, return partial
    if request.headers.get('HX-Request'):
        messages = thread.messages.select_related('sender').all()
        return render(request, 'sysadmin/partials/message_list.html', {
            'messages': messages,
            'thread': thread,
        })
    return redirect('sysadmin:support_detail', pk=pk)


# ── Inquiries ──────────────────────────────────────────

class SysadminInquiryListView(SuperuserRequiredMixin, ListView):
    model = Inquiry
    template_name = 'sysadmin/inquiry_list.html'
    context_object_name = 'inquiries'
    paginate_by = 20

    def get_queryset(self):
        return Inquiry.objects.select_related('contact', 'site').all()


@superuser_required
def sysadmin_inquiry_detail_view(request, pk):
    inquiry = get_object_or_404(
        Inquiry.objects.select_related('contact', 'site'), pk=pk
    )
    return render(request, 'sysadmin/inquiry_detail.html', {'inquiry': inquiry})


@superuser_required
def sysadmin_inquiry_reply_view(request, pk):
    if request.method != 'POST':
        return redirect('sysadmin:inquiry_detail', pk=pk)
    inquiry = get_object_or_404(Inquiry, pk=pk)
    reply = request.POST.get('admin_reply', '').strip()
    if reply:
        inquiry.admin_reply = reply
        inquiry.status = 'replied'
        inquiry.replied_at = timezone.now()
        inquiry.save(update_fields=['admin_reply', 'status', 'replied_at'])
    return redirect('sysadmin:inquiry_detail', pk=pk)


# --- マニュアル ---

SYSADMIN_MANUAL_CHAPTERS = [
    {'num': 1, 'title': 'システム管理の概要', 'desc': 'システム管理者の役割と管理画面の使い方'},
    {'num': 2, 'title': 'プロジェクト管理', 'desc': 'プロジェクト一覧・詳細・管理画面切替'},
    {'num': 3, 'title': 'ユーザー管理', 'desc': 'ユーザー一覧・詳細・有効化/無効化'},
    {'num': 4, 'title': 'サポート管理', 'desc': 'サポートスレッド・メッセージ・チャット対応'},
    {'num': 5, 'title': '問い合わせ管理', 'desc': '受講生からの問い合わせ確認・返信'},
]


@superuser_required
def sysadmin_manual_index_view(request):
    return render(request, 'sysadmin/manual_index.html', {
        'chapters': SYSADMIN_MANUAL_CHAPTERS,
    })


@superuser_required
def sysadmin_manual_chapter_view(request, chapter_num):
    if chapter_num < 1 or chapter_num > len(SYSADMIN_MANUAL_CHAPTERS):
        return redirect('sysadmin:manual_index')
    chapter = SYSADMIN_MANUAL_CHAPTERS[chapter_num - 1]
    prev_chapter = SYSADMIN_MANUAL_CHAPTERS[chapter_num - 2] if chapter_num > 1 else None
    next_chapter = SYSADMIN_MANUAL_CHAPTERS[chapter_num] if chapter_num < len(SYSADMIN_MANUAL_CHAPTERS) else None
    return render(request, 'sysadmin/manual_chapter.html', {
        'chapter': chapter,
        'chapter_template': f'sysadmin/manual/chapter_{chapter_num}.html',
        'prev_chapter': prev_chapter,
        'next_chapter': next_chapter,
    })
