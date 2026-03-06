from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.accounts.forms import SignupForm, ProjectForm
from apps.accounts.models import Project, ProjectMember, User
from apps.sysadmin.models import SupportThread, SupportMessage, Inquiry


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:project_create')
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        project = request.current_project
        if not project:
            return redirect('accounts:project_list')

        # 統計データを集計
        context = {
            'project': project,
            'contact_count': 0,
            'funnel_count': 0,
            'order_count': 0,
        }

        # コンタクト数
        try:
            from apps.contacts.models import Contact
            context['contact_count'] = Contact.objects.filter(project=project).count()
        except Exception:
            pass

        # ファネル数
        try:
            from apps.funnels.models import Funnel
            context['funnel_count'] = Funnel.objects.filter(project=project).count()
        except Exception:
            pass

        # 注文数
        try:
            from apps.products.models import Order
            context['order_count'] = Order.objects.filter(project=project).count()
        except Exception:
            pass

        return render(request, 'accounts/dashboard.html', context)


class ProjectListView(LoginRequiredMixin, View):
    def get(self, request):
        owned_projects = Project.objects.filter(owner=request.user)
        member_projects = Project.objects.filter(
            members__user=request.user
        ).exclude(owner=request.user)
        form = ProjectForm()
        context = {
            'owned_projects': owned_projects,
            'member_projects': member_projects,
            'form': form,
        }
        return render(request, 'accounts/project_list.html', context)


@login_required
def project_create_view(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            # オーナーを管理者として追加
            ProjectMember.objects.create(
                project=project,
                user=request.user,
                role='admin',
            )
            # セッションにプロジェクトIDをセット
            request.session['current_project_id'] = project.id
            return redirect('accounts:dashboard')
    else:
        form = ProjectForm()
    return render(request, 'accounts/project_create.html', {'form': form})


@login_required
def project_switch_view(request, slug):
    project = get_object_or_404(Project, slug=slug)
    # オーナーまたはメンバーであることを確認
    is_owner = project.owner == request.user
    is_member = project.members.filter(user=request.user).exists()
    if is_owner or is_member:
        request.session['current_project_id'] = project.id
    return redirect('accounts:dashboard')


# --- マニュアル ---

MANUAL_CHAPTERS = [
    {'num': 1, 'title': 'このシステムでできること', 'desc': 'システムの全体像と使うまでの流れ'},
    {'num': 2, 'title': 'はじめかた（アカウント作成とログイン）', 'desc': 'ユーザー登録・ログイン・プロジェクト作成'},
    {'num': 3, 'title': 'ダッシュボード（トップ画面）の見かた', 'desc': 'メニュー・統計カード・かんたん操作ボタン'},
    {'num': 4, 'title': 'コンタクト管理（お客さまリスト）', 'desc': '検索・タグ・詳細・編集'},
    {'num': 5, 'title': 'ファネル（集客ページ）を作る', 'desc': 'ページ作成・セクション編集・公開'},
    {'num': 6, 'title': 'メール配信', 'desc': 'シナリオ（ステップメール）と一斉配信'},
    {'num': 7, 'title': '商品と決済（お支払い）', 'desc': '商品登録・Stripe決済・注文管理'},
    {'num': 8, 'title': '会員サイト（学習コーナー）', 'desc': 'コース・レッスン・テスト・卒業証書・進捗管理'},
    {'num': 9, 'title': 'ひととおりの流れをやってみよう', 'desc': '全機能を使った実践チュートリアル'},
    {'num': 10, 'title': '困ったときは（よくある質問）', 'desc': 'Q&A 10問と用語集'},
    {'num': 11, 'title': 'オペレーター管理', 'desc': 'オペレーターの招待・権限設定・削除'},
    {'num': 12, 'title': 'サポート（システム管理者への連絡）', 'desc': 'サポートスレッド作成・チャット・ステータス管理'},
    {'num': 13, 'title': '受講生の問い合わせ管理', 'desc': '受講生からの問い合わせ確認・返信'},
    {'num': 14, 'title': '予約管理', 'desc': '予約タイプの作成・予約枠設定・予約一覧管理'},
]


class ManualIndexView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'manual/index.html', {'chapters': MANUAL_CHAPTERS})


class ManualChapterView(LoginRequiredMixin, View):
    def get(self, request, chapter_num):
        if chapter_num < 1 or chapter_num > len(MANUAL_CHAPTERS):
            return redirect('accounts:manual_index')
        chapter = MANUAL_CHAPTERS[chapter_num - 1]
        prev_chapter = MANUAL_CHAPTERS[chapter_num - 2] if chapter_num > 1 else None
        next_chapter = MANUAL_CHAPTERS[chapter_num] if chapter_num < len(MANUAL_CHAPTERS) else None
        return render(request, 'manual/chapter.html', {
            'chapter': chapter,
            'chapter_template': f'manual/chapters/chapter_{chapter_num}.html',
            'prev_chapter': prev_chapter,
            'next_chapter': next_chapter,
        })


# --- オペレーター管理 ---

class OperatorListView(LoginRequiredMixin, ListView):
    """オペレーター一覧"""
    model = ProjectMember
    template_name = 'accounts/operator_list.html'
    context_object_name = 'members'

    def dispatch(self, request, *args, **kwargs):
        project = getattr(request, 'current_project', None)
        if not project:
            return redirect('accounts:project_list')
        if project.owner != request.user:
            messages.error(request, 'この操作はプロジェクトオーナーのみ実行できます。')
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        project = self.request.current_project
        return ProjectMember.objects.filter(project=project).exclude(
            user=project.owner
        ).select_related('user')


@login_required
def operator_invite_view(request):
    """オペレーター招待"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')
    if project.owner != request.user:
        messages.error(request, 'この操作はプロジェクトオーナーのみ実行できます。')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, 'メールアドレスを入力してください。')
            return render(request, 'accounts/operator_invite.html')

        # ユーザーを取得、なければ作成
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            import secrets
            random_password = secrets.token_urlsafe(16)
            user = User.objects.create_user(
                username=email,
                email=email,
                password=random_password,
            )

        # 既にメンバーかチェック
        if ProjectMember.objects.filter(project=project, user=user).exists():
            messages.warning(request, 'このユーザーは既にメンバーです。')
            return redirect('accounts:operator_list')

        # ProjectMember作成（全権限ON）
        ProjectMember.objects.create(
            project=project,
            user=user,
            role='operator',
            can_manage_funnels=True,
            can_manage_emails=True,
            can_manage_members=True,
            can_manage_contacts=True,
            can_manage_products=True,
            can_manage_bookings=True,
        )
        messages.success(request, f'{email} をオペレーターとして招待しました。')
        return redirect('accounts:operator_list')

    return render(request, 'accounts/operator_invite.html')


@login_required
def operator_edit_view(request, pk):
    """オペレーター編集"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')
    if project.owner != request.user:
        messages.error(request, 'この操作はプロジェクトオーナーのみ実行できます。')
        return redirect('accounts:dashboard')

    member = get_object_or_404(ProjectMember, pk=pk, project=project)

    if request.method == 'POST':
        member.role = request.POST.get('role', 'operator')
        member.can_manage_funnels = 'can_manage_funnels' in request.POST
        member.can_manage_emails = 'can_manage_emails' in request.POST
        member.can_manage_members = 'can_manage_members' in request.POST
        member.can_manage_contacts = 'can_manage_contacts' in request.POST
        member.can_manage_products = 'can_manage_products' in request.POST
        member.can_manage_bookings = 'can_manage_bookings' in request.POST
        member.save()
        messages.success(request, '権限設定を更新しました。')
        return redirect('accounts:operator_list')

    return render(request, 'accounts/operator_edit.html', {
        'member': member,
    })


@login_required
def operator_delete_view(request, pk):
    """オペレーター削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')
    if project.owner != request.user:
        messages.error(request, 'この操作はプロジェクトオーナーのみ実行できます。')
        return redirect('accounts:dashboard')

    member = get_object_or_404(ProjectMember, pk=pk, project=project)

    if request.method == 'POST':
        member.delete()
        messages.success(request, 'メンバーを削除しました。')

    return redirect('accounts:operator_list')


# --- サポート（プロジェクト管理者 <-> システム管理者） ---

class ProjectSupportListView(LoginRequiredMixin, ListView):
    """プロジェクト管理者側サポートスレッド一覧"""
    model = SupportThread
    template_name = 'accounts/support_list.html'
    context_object_name = 'threads'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not getattr(request, 'current_project', None):
            return redirect('accounts:project_list')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return SupportThread.objects.filter(
            project=self.request.current_project
        ).annotate(message_count=Count('messages')).order_by('-updated_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_status'] = self.request.GET.get('status', '')
        return ctx


@login_required
def project_support_create_view(request):
    """サポートスレッド作成"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        if subject and body:
            thread = SupportThread.objects.create(
                project=project,
                subject=subject,
                created_by=request.user,
            )
            SupportMessage.objects.create(
                thread=thread,
                sender=request.user,
                body=body,
                is_from_admin=False,
            )
            messages.success(request, 'サポートスレッドを作成しました。')
            return redirect('accounts:support_detail', pk=thread.pk)
        else:
            messages.error(request, '件名と本文を入力してください。')

    return render(request, 'accounts/support_create.html')


@login_required
def project_support_detail_view(request, pk):
    """サポートスレッド詳細（チャット画面）"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    thread = get_object_or_404(SupportThread, pk=pk, project=project)
    thread_messages = thread.messages.select_related('sender').all()

    return render(request, 'accounts/support_detail.html', {
        'thread': thread,
        'thread_messages': thread_messages,
    })


@login_required
def project_support_reply_view(request, pk):
    """サポートスレッドに返信（HTMX対応）"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    if request.method != 'POST':
        return redirect('accounts:support_detail', pk=pk)

    thread = get_object_or_404(SupportThread, pk=pk, project=project)
    body = request.POST.get('body', '').strip()
    if body:
        SupportMessage.objects.create(
            thread=thread,
            sender=request.user,
            body=body,
            is_from_admin=False,
        )
        thread.status = 'open'
        thread.save(update_fields=['status', 'updated_at'])

    if request.headers.get('HX-Request'):
        thread_messages = thread.messages.select_related('sender').all()
        return render(request, 'accounts/partials/support_message_list.html', {
            'thread_messages': thread_messages,
            'thread': thread,
        })
    return redirect('accounts:support_detail', pk=pk)


# --- 問い合わせ管理（プロジェクト管理者側） ---

class ProjectInquiryListView(LoginRequiredMixin, ListView):
    """プロジェクト管理者側問い合わせ一覧"""
    model = Inquiry
    template_name = 'accounts/inquiry_list.html'
    context_object_name = 'inquiries'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not getattr(request, 'current_project', None):
            return redirect('accounts:project_list')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Inquiry.objects.filter(
            site__project=self.request.current_project
        ).select_related('contact', 'site').order_by('-created_at')


@login_required
def project_inquiry_detail_view(request, pk):
    """問い合わせ詳細"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    inquiry = get_object_or_404(
        Inquiry.objects.select_related('contact', 'site'),
        pk=pk, site__project=project
    )
    return render(request, 'accounts/inquiry_detail.html', {'inquiry': inquiry})


@login_required
def project_inquiry_reply_view(request, pk):
    """問い合わせに返信"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    if request.method != 'POST':
        return redirect('accounts:inquiry_detail', pk=pk)

    inquiry = get_object_or_404(Inquiry, pk=pk, site__project=project)
    reply = request.POST.get('admin_reply', '').strip()
    if reply:
        inquiry.admin_reply = reply
        inquiry.status = 'replied'
        inquiry.replied_at = timezone.now()
        inquiry.save(update_fields=['admin_reply', 'status', 'replied_at'])
        messages.success(request, '返信を送信しました。')
    return redirect('accounts:inquiry_detail', pk=pk)
