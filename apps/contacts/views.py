from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView

from apps.accounts.decorators import project_permission_required
from apps.contacts.models import Contact, Tag, ContactTag, ActivityLog


@method_decorator(project_permission_required('can_manage_contacts'), name='dispatch')
class ContactListView(LoginRequiredMixin, ListView):
    """コンタクト一覧"""
    model = Contact
    template_name = 'contacts/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 50

    def get_queryset(self):
        project = self.request.current_project
        qs = Contact.objects.filter(project=project).prefetch_related('contact_tags__tag')

        # 検索
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q))

        # タグフィルタ
        tag_id = self.request.GET.get('tag', '').strip()
        if tag_id:
            qs = qs.filter(contact_tags__tag_id=tag_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.request.current_project
        context['tags'] = Tag.objects.filter(project=project)
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_tag'] = self.request.GET.get('tag', '')
        context['total_count'] = Contact.objects.filter(project=project).count()
        return context


@method_decorator(project_permission_required('can_manage_contacts'), name='dispatch')
class ContactDetailView(LoginRequiredMixin, DetailView):
    """コンタクト詳細"""
    model = Contact
    template_name = 'contacts/contact_detail.html'
    context_object_name = 'contact'

    def get_queryset(self):
        project = self.request.current_project
        return Contact.objects.filter(project=project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.object
        context['contact_tags'] = contact.contact_tags.select_related('tag').all()
        context['activities'] = contact.activities.all()[:50]
        context['all_tags'] = Tag.objects.filter(project=self.request.current_project)
        return context


@login_required
@project_permission_required('can_manage_contacts')
def contact_edit_view(request, pk):
    """コンタクト編集"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    contact = get_object_or_404(Contact, pk=pk, project=project)
    all_tags = Tag.objects.filter(project=project)

    if request.method == 'POST':
        # 基本情報の更新
        contact.name = request.POST.get('name', '').strip()
        contact.email = request.POST.get('email', '').strip()
        contact.phone = request.POST.get('phone', '').strip()
        contact.memo = request.POST.get('memo', '').strip()
        contact.save()

        # タグの更新
        selected_tag_ids = request.POST.getlist('tags')
        current_tag_ids = set(
            contact.contact_tags.values_list('tag_id', flat=True)
        )
        new_tag_ids = set(int(tid) for tid in selected_tag_ids if tid)

        # 削除するタグ
        tags_to_remove = current_tag_ids - new_tag_ids
        if tags_to_remove:
            ContactTag.objects.filter(
                contact=contact, tag_id__in=tags_to_remove
            ).delete()

        # 追加するタグ
        tags_to_add = new_tag_ids - current_tag_ids
        for tag_id in tags_to_add:
            ContactTag.objects.get_or_create(
                contact=contact,
                tag_id=tag_id,
            )

        # アクティビティログ記録
        ActivityLog.objects.create(
            contact=contact,
            action='profile_updated',
            detail={'updated_by': request.user.username},
        )

        return redirect('contacts:contact_detail', pk=contact.pk)

    # GET
    contact_tag_ids = set(
        contact.contact_tags.values_list('tag_id', flat=True)
    )
    context = {
        'contact': contact,
        'all_tags': all_tags,
        'contact_tag_ids': contact_tag_ids,
    }
    return render(request, 'contacts/contact_edit.html', context)
