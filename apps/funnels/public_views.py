from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from apps.contacts.models import Contact, ActivityLog
from apps.funnels.models import Funnel, FunnelPage


def public_page_view(request, funnel_slug, page_slug):
    """公開ファネルページの表示"""
    funnel = get_object_or_404(Funnel, slug=funnel_slug, is_published=True)
    page = get_object_or_404(FunnelPage, funnel=funnel, slug=page_slug)
    sections = page.sections.filter(is_visible=True).order_by('sort_order')

    # セクションデータを加工（video URLをembed URLに変換など）
    processed_sections = []
    for section in sections:
        data = {
            'section_type': section.section_type,
            'content': section.content,
            'pk': section.pk,
        }

        # YouTube/Vimeo URLをembed URLに変換
        if section.section_type == 'video':
            video_url = section.content.get('video_url', '')
            data['embed_url'] = convert_to_embed_url(video_url)

        processed_sections.append(data)

    meta_title = page.meta_title or page.title
    meta_description = page.meta_description or ''

    return render(request, 'funnels/public/page_render.html', {
        'funnel': funnel,
        'page': page,
        'sections': processed_sections,
        'meta_title': meta_title,
        'meta_description': meta_description,
    })


@csrf_exempt
def form_submit_view(request):
    """フォームセクションのサブミット処理"""
    if request.method != 'POST':
        raise Http404

    email = request.POST.get('email', '').strip()
    name = request.POST.get('name', '').strip()
    funnel_id = request.POST.get('funnel_id', '')
    page_id = request.POST.get('page_id', '')
    scenario_id = request.POST.get('scenario_id', '')
    redirect_url = request.POST.get('redirect_url', '')

    if not email:
        raise Http404

    # ファネルからプロジェクトを特定
    try:
        funnel = Funnel.objects.get(pk=funnel_id)
        project = funnel.project
    except (Funnel.DoesNotExist, ValueError):
        raise Http404

    # コンタクトを作成または更新
    contact, created = Contact.objects.get_or_create(
        project=project,
        email=email,
        defaults={'name': name},
    )
    if not created and name:
        contact.name = name
        contact.save()

    # アクティビティログに form_submit を記録
    ActivityLog.objects.create(
        contact=contact,
        action='form_submit',
        detail={
            'funnel_id': funnel_id,
            'page_id': page_id,
            'funnel_name': funnel.name,
        },
    )

    # scenario_id があればシナリオ登録を試みる
    if scenario_id:
        try:
            from apps.emails.models import Scenario, ScenarioSubscription
            scenario = Scenario.objects.get(pk=scenario_id, project=project)
            ScenarioSubscription.objects.get_or_create(
                scenario=scenario,
                contact=contact,
            )
        except Exception:
            # シナリオモデルが未実装の場合はスキップ
            pass

    # リダイレクト
    if redirect_url:
        return redirect(redirect_url)

    # redirect_url が未設定の場合、サンクスページを探す
    try:
        thanks_page = FunnelPage.objects.filter(
            funnel=funnel, page_type='thanks'
        ).first()
        if thanks_page:
            return redirect(
                'funnels_public:public_page',
                funnel_slug=funnel.slug,
                page_slug=thanks_page.slug,
            )
    except Exception:
        pass

    # フォールバック: シンプルなサンクスメッセージ
    return render(request, 'funnels/public/thanks_fallback.html', {
        'funnel': funnel,
    })


def convert_to_embed_url(url):
    """YouTube/Vimeo URLをembed URLに変換"""
    if not url:
        return ''

    # YouTube
    if 'youtube.com/watch' in url:
        video_id = ''
        if 'v=' in url:
            video_id = url.split('v=')[1].split('&')[0]
        if video_id:
            return f'https://www.youtube.com/embed/{video_id}'

    if 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[1].split('?')[0]
        if video_id:
            return f'https://www.youtube.com/embed/{video_id}'

    # Vimeo
    if 'vimeo.com/' in url:
        parts = url.rstrip('/').split('/')
        video_id = parts[-1]
        if video_id.isdigit():
            return f'https://player.vimeo.com/video/{video_id}'

    # その他はそのまま返す
    return url
