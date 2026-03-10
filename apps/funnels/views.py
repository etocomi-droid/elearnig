import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models as db_models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView

from django.utils.decorators import method_decorator

from apps.accounts.decorators import project_permission_required
from apps.funnels.forms import FunnelForm, FunnelPageForm
from apps.funnels.models import Funnel, FunnelPage, PageSection


# ---------- デフォルトコンテンツ ----------

SECTION_DEFAULTS = {
    'hero': {
        'headline': '大きな見出しテキスト',
        'subheadline': 'サブ見出しテキスト',
        'bg_color': '#1e40af',
    },
    'text': {
        'body': '<p>ここにテキストを入力してください。</p>',
    },
    'image': {
        'image_url': '',
        'alt_text': '',
    },
    'video': {
        'video_url': '',
    },
    'button': {
        'label': '今すぐ申し込む',
        'url': '#',
        'color': '#2563eb',
        'size': 'md',
    },
    'form': {
        'fields': ['email'],
        'submit_label': '無料で登録する',
        'scenario_id': '',
        'redirect_url': '',
    },
    'countdown': {
        'target_date': '',
        'label': '締め切りまで',
    },
    'testimonial': {
        'name': 'お客様の名前',
        'text': 'お客様の声をここに入力してください。',
        'image_url': '',
    },
    'faq': {
        'items': [
            {'question': 'よくある質問', 'answer': '回答をここに入力してください。'},
        ],
    },
    'schedule': {
        'booking_type_id': '',
        'heading': '日程をお選びください',
        'description': '',
        'accent_color': '#2563eb',
    },
    'meeting': {
        'booking_type_id': '',
        'heading': '面談の日程をお選びください',
        'description': '',
        'accent_color': '#7c3aed',
    },
    'separator': {},
}


# ---------- ファネル一覧 ----------

@method_decorator(project_permission_required('can_manage_funnels'), name='dispatch')
class FunnelListView(LoginRequiredMixin, ListView):
    """ファネル一覧"""
    model = Funnel
    template_name = 'funnels/funnel_list.html'
    context_object_name = 'funnels'

    def get_queryset(self):
        qs = Funnel.objects.filter(
            project=self.request.current_project
        ).prefetch_related('pages').order_by('-created_at')
        site_id = self.request.GET.get('site')
        if site_id:
            qs = qs.filter(site_id=site_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_id = self.request.GET.get('site')
        if site_id:
            from apps.members.models import MemberSite
            context['current_site'] = MemberSite.objects.filter(
                pk=site_id, project=self.request.current_project
            ).first()
        return context


# ---------- ファネル作成 ----------

@login_required
@project_permission_required('can_manage_funnels')
def funnel_create_view(request):
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    site_id = request.GET.get('site') or request.POST.get('site')
    site = None
    if site_id:
        from apps.members.models import MemberSite
        site = get_object_or_404(MemberSite, pk=site_id, project=project)

    if request.method == 'POST':
        form = FunnelForm(request.POST)
        if form.is_valid():
            funnel = form.save(commit=False)
            funnel.project = project
            funnel.site = site
            funnel.save()
            messages.success(request, f'ファネル「{funnel.name}」を作成しました。')
            redirect_url = f"{'funnels:funnel_edit'}"
            return redirect('funnels:funnel_edit', pk=funnel.pk)
    else:
        form = FunnelForm()

    return render(request, 'funnels/funnel_form.html', {
        'form': form,
        'is_create': True,
        'current_site': site,
    })


# ---------- ファネル編集 ----------

@login_required
@project_permission_required('can_manage_funnels')
def funnel_edit_view(request, pk):
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    funnel = get_object_or_404(Funnel, pk=pk, project=project)

    if request.method == 'POST':
        form = FunnelForm(request.POST, instance=funnel)
        if form.is_valid():
            form.save()
            messages.success(request, 'ファネル情報を更新しました。')
            return redirect('funnels:funnel_edit', pk=funnel.pk)
    else:
        form = FunnelForm(instance=funnel)

    pages = funnel.pages.all()

    return render(request, 'funnels/funnel_edit.html', {
        'form': form,
        'funnel': funnel,
        'pages': pages,
    })


# ---------- ファネル削除 ----------

@login_required
@project_permission_required('can_manage_funnels')
def funnel_delete_view(request, pk):
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    funnel = get_object_or_404(Funnel, pk=pk, project=project)

    if request.method == 'POST':
        name = funnel.name
        funnel.delete()
        messages.success(request, f'ファネル「{name}」を削除しました。')
        return redirect('funnels:funnel_list')

    return render(request, 'funnels/funnel_delete.html', {
        'funnel': funnel,
    })


# ---------- ページ作成 ----------

@login_required
@project_permission_required('can_manage_funnels')
def page_create_view(request, funnel_id):
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    funnel = get_object_or_404(Funnel, pk=funnel_id, project=project)

    if request.method == 'POST':
        form = FunnelPageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.funnel = funnel
            # 表示順を最後に設定
            max_order = funnel.pages.aggregate(
                max_order=db_models.Max('sort_order')
            )['max_order'] or 0
            page.sort_order = max_order + 1
            page.save()
            messages.success(request, f'ページ「{page.title}」を追加しました。')
            return redirect('funnels:page_edit', pk=page.pk)
    else:
        form = FunnelPageForm()

    return render(request, 'funnels/page_form.html', {
        'form': form,
        'funnel': funnel,
        'is_create': True,
    })


# ---------- ページ編集 ----------

@login_required
@project_permission_required('can_manage_funnels')
def page_edit_view(request, pk):
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    page = get_object_or_404(
        FunnelPage.objects.select_related('funnel'),
        pk=pk,
        funnel__project=project
    )

    if request.method == 'POST':
        form = FunnelPageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            messages.success(request, 'ページ情報を更新しました。')
            return redirect('funnels:page_edit', pk=page.pk)
    else:
        form = FunnelPageForm(instance=page)

    sections = page.sections.all()

    return render(request, 'funnels/page_edit.html', {
        'form': form,
        'page': page,
        'funnel': page.funnel,
        'sections': sections,
        'section_type_choices': PageSection.SECTION_TYPE_CHOICES,
    })


# ---------- ページ削除 ----------

@login_required
@project_permission_required('can_manage_funnels')
def page_delete_view(request, pk):
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    page = get_object_or_404(
        FunnelPage.objects.select_related('funnel'),
        pk=pk,
        funnel__project=project
    )
    funnel = page.funnel

    if request.method == 'POST':
        title = page.title
        page.delete()
        messages.success(request, f'ページ「{title}」を削除しました。')
        return redirect('funnels:funnel_edit', pk=funnel.pk)

    return render(request, 'funnels/page_delete.html', {
        'page': page,
        'funnel': funnel,
    })


# ---------- セクション追加 (HTMX) ----------

@login_required
@project_permission_required('can_manage_funnels')
def section_add_view(request, page_id):
    project = getattr(request, 'current_project', None)
    if not project:
        return HttpResponse(status=403)

    page = get_object_or_404(
        FunnelPage.objects.select_related('funnel'),
        pk=page_id,
        funnel__project=project
    )

    if request.method == 'POST':
        section_type = request.POST.get('section_type', 'text')
        default_content = SECTION_DEFAULTS.get(section_type, {}).copy()

        max_order = page.sections.aggregate(
            max_order=db_models.Max('sort_order')
        )['max_order'] or 0

        section = PageSection.objects.create(
            page=page,
            section_type=section_type,
            content=default_content,
            sort_order=max_order + 1,
        )

        # HTMX: セクションリストを返す
        sections = page.sections.all()
        return render(request, 'funnels/partials/section_list.html', {
            'sections': sections,
            'page': page,
        })

    return HttpResponse(status=405)


# ---------- セクション編集 (HTMX) ----------

@login_required
@project_permission_required('can_manage_funnels')
def section_edit_view(request, pk):
    project = getattr(request, 'current_project', None)
    if not project:
        return HttpResponse(status=403)

    section = get_object_or_404(
        PageSection.objects.select_related('page__funnel'),
        pk=pk,
        page__funnel__project=project
    )

    if request.method == 'POST':
        # コンテンツをセクションタイプに応じて更新
        content = {}
        st = section.section_type

        if st == 'hero':
            content['headline'] = request.POST.get('headline', '')
            content['subheadline'] = request.POST.get('subheadline', '')
            content['bg_color'] = request.POST.get('bg_color', '#1e40af')
        elif st == 'text':
            content['body'] = request.POST.get('body', '')
        elif st == 'image':
            content['image_url'] = request.POST.get('image_url', '')
            content['alt_text'] = request.POST.get('alt_text', '')
        elif st == 'video':
            content['video_url'] = request.POST.get('video_url', '')
        elif st == 'button':
            content['label'] = request.POST.get('label', '')
            content['url'] = request.POST.get('url', '')
            content['color'] = request.POST.get('color', '#2563eb')
            content['size'] = request.POST.get('size', 'md')
        elif st == 'form':
            content['fields'] = ['email']
            content['submit_label'] = request.POST.get('submit_label', '')
            content['scenario_id'] = request.POST.get('scenario_id', '')
            content['redirect_url'] = request.POST.get('redirect_url', '')
        elif st == 'countdown':
            content['target_date'] = request.POST.get('target_date', '')
            content['label'] = request.POST.get('label', '')
        elif st == 'testimonial':
            content['name'] = request.POST.get('testimonial_name', '')
            content['text'] = request.POST.get('testimonial_text', '')
            content['image_url'] = request.POST.get('image_url', '')
        elif st == 'faq':
            questions = request.POST.getlist('faq_question')
            answers = request.POST.getlist('faq_answer')
            items = []
            for q, a in zip(questions, answers):
                if q.strip() or a.strip():
                    items.append({'question': q, 'answer': a})
            content['items'] = items if items else [{'question': '', 'answer': ''}]
        elif st in ('schedule', 'meeting'):
            content['booking_type_id'] = request.POST.get('booking_type_id', '')
            content['heading'] = request.POST.get('heading', '')
            content['description'] = request.POST.get('description', '')
            content['accent_color'] = request.POST.get('accent_color', '#2563eb')
        # separator は設定なし

        section.content = content
        section.is_visible = 'is_visible' in request.POST
        section.save()

        # HTMX: 更新済みセクションリストを返す
        sections = section.page.sections.all()
        return render(request, 'funnels/partials/section_list.html', {
            'sections': sections,
            'page': section.page,
        })

    # GET: 編集フォームを返す
    context = {'section': section}
    if section.section_type in ('schedule', 'meeting'):
        from apps.bookings.models import BookingType
        context['booking_types'] = BookingType.objects.filter(
            project=project, is_active=True
        )
    return render(request, 'funnels/partials/section_form.html', context)


# ---------- セクション削除 (HTMX) ----------

@login_required
@project_permission_required('can_manage_funnels')
def section_delete_view(request, pk):
    project = getattr(request, 'current_project', None)
    if not project:
        return HttpResponse(status=403)

    section = get_object_or_404(
        PageSection.objects.select_related('page__funnel'),
        pk=pk,
        page__funnel__project=project
    )

    if request.method == 'POST':
        page = section.page
        section.delete()

        # HTMX: 更新済みセクションリストを返す
        sections = page.sections.all()
        return render(request, 'funnels/partials/section_list.html', {
            'sections': sections,
            'page': page,
        })

    return HttpResponse(status=405)


# ---------- セクション並び替え (HTMX) ----------

@login_required
@project_permission_required('can_manage_funnels')
def section_reorder_view(request, page_id):
    project = getattr(request, 'current_project', None)
    if not project:
        return HttpResponse(status=403)

    page = get_object_or_404(
        FunnelPage.objects.select_related('funnel'),
        pk=page_id,
        funnel__project=project
    )

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            order_ids = body.get('order', [])
        except (json.JSONDecodeError, AttributeError):
            # フォームデータからも試す
            order_str = request.POST.get('order', '[]')
            try:
                order_ids = json.loads(order_str)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid data'}, status=400)

        for i, section_id in enumerate(order_ids):
            PageSection.objects.filter(
                pk=section_id, page=page
            ).update(sort_order=i)

        return HttpResponse(status=200)

    return HttpResponse(status=405)
