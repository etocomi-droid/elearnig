from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView

from django.utils.decorators import method_decorator

from apps.accounts.decorators import project_permission_required
from apps.contacts.models import Contact, ContactTag, ActivityLog
from apps.emails.forms import ScenarioForm, ScenarioStepForm, CampaignForm
from apps.emails.models import (
    Scenario, ScenarioStep, ScenarioSubscription,
    Campaign, EmailLog,
)


# =============================================================================
# シナリオ関連ビュー
# =============================================================================

@method_decorator(project_permission_required('can_manage_emails'), name='dispatch')
class ScenarioListView(LoginRequiredMixin, ListView):
    """シナリオ一覧"""
    model = Scenario
    template_name = 'emails/scenario_list.html'
    context_object_name = 'scenarios'
    paginate_by = 20

    def get_queryset(self):
        project = self.request.current_project
        return (
            Scenario.objects
            .filter(project=project)
            .annotate(
                step_count=Count('steps', distinct=True),
                subscriber_count=Count('subscriptions', distinct=True),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = Scenario.objects.filter(
            project=self.request.current_project
        ).count()
        return context


@login_required
@project_permission_required('can_manage_emails')
def scenario_create_view(request):
    """シナリオ作成"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    if request.method == 'POST':
        form = ScenarioForm(request.POST)
        if form.is_valid():
            scenario = form.save(commit=False)
            scenario.project = project
            scenario.save()
            messages.success(request, f'シナリオ「{scenario.name}」を作成しました。')
            return redirect('emails:scenario_edit', pk=scenario.pk)
    else:
        form = ScenarioForm()

    return render(request, 'emails/scenario_edit.html', {
        'form': form,
        'is_new': True,
    })


@login_required
@project_permission_required('can_manage_emails')
def scenario_edit_view(request, pk):
    """シナリオ編集 + ステップ一覧表示"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    scenario = get_object_or_404(Scenario, pk=pk, project=project)
    steps = scenario.steps.all()

    if request.method == 'POST':
        form = ScenarioForm(request.POST, instance=scenario)
        if form.is_valid():
            form.save()
            messages.success(request, f'シナリオ「{scenario.name}」を更新しました。')
            return redirect('emails:scenario_edit', pk=scenario.pk)
    else:
        form = ScenarioForm(instance=scenario)

    return render(request, 'emails/scenario_edit.html', {
        'form': form,
        'scenario': scenario,
        'steps': steps,
        'is_new': False,
    })


@login_required
@project_permission_required('can_manage_emails')
def scenario_delete_view(request, pk):
    """シナリオ削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    scenario = get_object_or_404(Scenario, pk=pk, project=project)

    if request.method == 'POST':
        name = scenario.name
        scenario.delete()
        messages.success(request, f'シナリオ「{name}」を削除しました。')
        return redirect('emails:scenario_list')

    return render(request, 'emails/scenario_delete_confirm.html', {
        'scenario': scenario,
    })


# =============================================================================
# ステップ関連ビュー
# =============================================================================

@login_required
@project_permission_required('can_manage_emails')
def step_create_view(request, scenario_id):
    """ステップ追加"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    scenario = get_object_or_404(Scenario, pk=scenario_id, project=project)

    # 次のステップ番号を自動算出
    last_step = scenario.steps.order_by('-step_number').first()
    next_step_number = (last_step.step_number + 1) if last_step else 1

    if request.method == 'POST':
        form = ScenarioStepForm(request.POST)
        if form.is_valid():
            step = form.save(commit=False)
            step.scenario = scenario
            step.save()
            messages.success(request, f'ステップ {step.step_number} を追加しました。')
            return redirect('emails:scenario_edit', pk=scenario.pk)
    else:
        form = ScenarioStepForm(initial={'step_number': next_step_number})

    return render(request, 'emails/step_edit.html', {
        'form': form,
        'scenario': scenario,
        'is_new': True,
    })


@login_required
@project_permission_required('can_manage_emails')
def step_edit_view(request, scenario_id, pk):
    """ステップ編集"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    scenario = get_object_or_404(Scenario, pk=scenario_id, project=project)
    step = get_object_or_404(ScenarioStep, pk=pk, scenario=scenario)

    if request.method == 'POST':
        form = ScenarioStepForm(request.POST, instance=step)
        if form.is_valid():
            form.save()
            messages.success(request, f'ステップ {step.step_number} を更新しました。')
            return redirect('emails:scenario_edit', pk=scenario.pk)
    else:
        form = ScenarioStepForm(instance=step)

    return render(request, 'emails/step_edit.html', {
        'form': form,
        'scenario': scenario,
        'step': step,
        'is_new': False,
    })


@login_required
@project_permission_required('can_manage_emails')
def step_delete_view(request, scenario_id, pk):
    """ステップ削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    scenario = get_object_or_404(Scenario, pk=scenario_id, project=project)
    step = get_object_or_404(ScenarioStep, pk=pk, scenario=scenario)

    if request.method == 'POST':
        step_number = step.step_number
        step.delete()
        messages.success(request, f'ステップ {step_number} を削除しました。')
        return redirect('emails:scenario_edit', pk=scenario.pk)

    return render(request, 'emails/step_delete_confirm.html', {
        'scenario': scenario,
        'step': step,
    })


# =============================================================================
# 一斉配信（キャンペーン）関連ビュー
# =============================================================================

@method_decorator(project_permission_required('can_manage_emails'), name='dispatch')
class CampaignListView(LoginRequiredMixin, ListView):
    """一斉配信一覧"""
    model = Campaign
    template_name = 'emails/campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 20

    def get_queryset(self):
        return Campaign.objects.filter(project=self.request.current_project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = Campaign.objects.filter(
            project=self.request.current_project
        ).count()
        return context


@login_required
@project_permission_required('can_manage_emails')
def campaign_create_view(request):
    """一斉配信作成"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    if request.method == 'POST':
        form = CampaignForm(request.POST, project=project)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.project = project
            campaign.save()
            form.save_m2m()  # ManyToMany の target_tags を保存
            messages.success(request, f'一斉配信「{campaign.name}」を作成しました。')
            return redirect('emails:campaign_edit', pk=campaign.pk)
    else:
        form = CampaignForm(project=project)

    return render(request, 'emails/campaign_edit.html', {
        'form': form,
        'is_new': True,
    })


@login_required
@project_permission_required('can_manage_emails')
def campaign_edit_view(request, pk):
    """一斉配信編集"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    campaign = get_object_or_404(Campaign, pk=pk, project=project)

    if request.method == 'POST':
        form = CampaignForm(request.POST, instance=campaign, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'一斉配信「{campaign.name}」を更新しました。')
            return redirect('emails:campaign_edit', pk=campaign.pk)
    else:
        form = CampaignForm(instance=campaign, project=project)

    return render(request, 'emails/campaign_edit.html', {
        'form': form,
        'campaign': campaign,
        'is_new': False,
    })


@login_required
@project_permission_required('can_manage_emails')
def campaign_delete_view(request, pk):
    """一斉配信削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    campaign = get_object_or_404(Campaign, pk=pk, project=project)

    if request.method == 'POST':
        name = campaign.name
        campaign.delete()
        messages.success(request, f'一斉配信「{name}」を削除しました。')
        return redirect('emails:campaign_list')

    return render(request, 'emails/campaign_delete_confirm.html', {
        'campaign': campaign,
    })


@login_required
@project_permission_required('can_manage_emails')
def campaign_send_view(request, pk):
    """一斉配信送信実行"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    campaign = get_object_or_404(Campaign, pk=pk, project=project)

    if campaign.status != 'draft':
        messages.error(request, 'この一斉配信は既に送信済みか、送信中です。')
        return redirect('emails:campaign_edit', pk=campaign.pk)

    if request.method == 'POST':
        # ステータスを「送信中」に更新
        campaign.status = 'sending'
        campaign.save()

        # ターゲットコンタクトを取得
        target_tags = campaign.target_tags.all()
        if target_tags.exists():
            # タグが指定されている場合、そのタグを持つコンタクトを取得
            contact_ids = (
                ContactTag.objects
                .filter(tag__in=target_tags)
                .values_list('contact_id', flat=True)
                .distinct()
            )
            contacts = Contact.objects.filter(
                pk__in=contact_ids,
                project=project,
            )
        else:
            # タグ未指定の場合、プロジェクト全コンタクト
            contacts = Contact.objects.filter(project=project)

        sent_count = 0
        failed_count = 0

        for contact in contacts:
            try:
                send_mail(
                    subject=campaign.subject,
                    message=campaign.body_text or '',
                    from_email=None,  # settings.DEFAULT_FROM_EMAIL を使用
                    recipient_list=[contact.email],
                    html_message=campaign.body_html,
                    fail_silently=False,
                )
                EmailLog.objects.create(
                    contact=contact,
                    subject=campaign.subject,
                    email_type='campaign',
                    status='sent',
                    campaign=campaign,
                )
                sent_count += 1
            except Exception:
                EmailLog.objects.create(
                    contact=contact,
                    subject=campaign.subject,
                    email_type='campaign',
                    status='failed',
                    campaign=campaign,
                )
                failed_count += 1

            # アクティビティログに記録
            ActivityLog.objects.create(
                contact=contact,
                action='campaign_email_sent',
                detail={
                    'campaign_id': campaign.pk,
                    'campaign_name': campaign.name,
                    'subject': campaign.subject,
                },
            )

        # ステータスを「送信済み」に更新
        campaign.status = 'sent'
        campaign.sent_at = timezone.now()
        campaign.save()

        messages.success(
            request,
            f'一斉配信「{campaign.name}」を送信しました。'
            f'（成功: {sent_count}件、失敗: {failed_count}件）'
        )
        return redirect('emails:campaign_list')

    # GET の場合は確認画面を表示
    # ターゲットコンタクト数を計算
    target_tags = campaign.target_tags.all()
    if target_tags.exists():
        contact_ids = (
            ContactTag.objects
            .filter(tag__in=target_tags)
            .values_list('contact_id', flat=True)
            .distinct()
        )
        target_count = Contact.objects.filter(
            pk__in=contact_ids,
            project=project,
        ).count()
    else:
        target_count = Contact.objects.filter(project=project).count()

    return render(request, 'emails/campaign_send_confirm.html', {
        'campaign': campaign,
        'target_count': target_count,
    })
