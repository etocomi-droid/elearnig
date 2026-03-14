from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from apps.accounts.decorators import project_permission_required
from apps.members.forms import MemberSiteForm, CourseForm, LessonForm, QuizForm, QuestionForm, ChoiceFormSet, CertificateForm
from apps.members.models import MemberSite, Course, Lesson, Enrollment, Quiz, Question, Choice, QuizAttempt, Certificate


@method_decorator(project_permission_required('can_manage_members'), name='dispatch')
class SiteListView(LoginRequiredMixin, ListView):
    """会員サイト一覧"""
    model = MemberSite
    template_name = 'members/site_list.html'
    context_object_name = 'sites'

    def get_queryset(self):
        project = self.request.current_project
        return MemberSite.objects.filter(project=project).annotate(
            course_count=Count('courses', distinct=True),
            member_count=Count('courses__enrollments__contact', distinct=True),
        )


@login_required
@project_permission_required('can_manage_members')
def site_create_view(request):
    """会員サイト作成"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    if request.method == 'POST':
        form = MemberSiteForm(request.POST)
        if form.is_valid():
            site = form.save(commit=False)
            site.project = project
            site.save()
            messages.success(request, f'会員サイト「{site.name}」を作成しました。')
            return redirect('members:site_edit', pk=site.pk)
    else:
        form = MemberSiteForm()

    return render(request, 'members/site_edit.html', {
        'form': form,
        'is_new': True,
    })


@login_required
@project_permission_required('can_manage_members')
def site_edit_view(request, pk):
    """会員サイト編集 + コース一覧"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    site = get_object_or_404(MemberSite, pk=pk, project=project)

    if request.method == 'POST':
        form = MemberSiteForm(request.POST, instance=site)
        if form.is_valid():
            form.save()
            messages.success(request, 'サイト情報を更新しました。')
            return redirect('members:site_edit', pk=site.pk)
    else:
        form = MemberSiteForm(instance=site)

    courses = site.courses.annotate(
        lesson_count=Count('lessons'),
    ).order_by('sort_order')

    # サイトに紐づくファネル・シナリオ・キャンペーン
    site_funnels = site.funnels.all().order_by('-created_at')[:10]
    site_scenarios = site.scenarios.annotate(
        step_count=Count('steps', distinct=True),
    ).order_by('-created_at')[:10]
    site_campaigns = site.campaigns.all().order_by('-created_at')[:10]

    return render(request, 'members/site_edit.html', {
        'form': form,
        'site': site,
        'courses': courses,
        'site_funnels': site_funnels,
        'site_scenarios': site_scenarios,
        'site_campaigns': site_campaigns,
        'is_new': False,
    })


@login_required
@project_permission_required('can_manage_members')
def course_create_view(request):
    """コース作成"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    site_id = request.GET.get('site') or request.POST.get('site')
    site = get_object_or_404(MemberSite, pk=site_id, project=project)

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.site = site
            # 自動で表示順をセット
            max_order = site.courses.aggregate(max_order=Count('id'))['max_order'] or 0
            course.sort_order = max_order
            course.save()
            messages.success(request, f'コース「{course.title}」を作成しました。')
            return redirect('members:course_edit', pk=course.pk)
    else:
        form = CourseForm()

    return render(request, 'members/course_edit.html', {
        'form': form,
        'site': site,
        'is_new': True,
    })


@login_required
@project_permission_required('can_manage_members')
def course_edit_view(request, pk):
    """コース編集 + レッスン一覧"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    course = get_object_or_404(Course, pk=pk, site__project=project)
    site = course.site

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'コース情報を更新しました。')
            return redirect('members:course_edit', pk=course.pk)
    else:
        form = CourseForm(instance=course)

    lessons = course.lessons.select_related('quiz').all()

    return render(request, 'members/course_edit.html', {
        'form': form,
        'site': site,
        'course': course,
        'lessons': lessons,
        'is_new': False,
    })


@login_required
@project_permission_required('can_manage_members')
def course_delete_view(request, pk):
    """コース削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    course = get_object_or_404(Course, pk=pk, site__project=project)
    site = course.site

    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(request, f'コース「{course_title}」を削除しました。')
        return redirect('members:site_edit', pk=site.pk)

    return render(request, 'members/course_delete_confirm.html', {
        'course': course,
        'site': site,
    })


@login_required
@project_permission_required('can_manage_members')
def lesson_create_view(request):
    """レッスン作成"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    course_id = request.GET.get('course') or request.POST.get('course')
    course = get_object_or_404(Course, pk=course_id, site__project=project)

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            # 自動で表示順をセット
            max_order = course.lessons.count()
            lesson.sort_order = max_order
            lesson.save()
            messages.success(request, f'レッスン「{lesson.title}」を作成しました。')
            return redirect('members:lesson_edit', pk=lesson.pk)
    else:
        form = LessonForm()

    return render(request, 'members/lesson_edit.html', {
        'form': form,
        'course': course,
        'site': course.site,
        'is_new': True,
    })


@login_required
@project_permission_required('can_manage_members')
def lesson_edit_view(request, pk):
    """レッスン編集"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    lesson = get_object_or_404(Lesson, pk=pk, course__site__project=project)
    course = lesson.course
    site = course.site

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, 'レッスン情報を更新しました。')
            return redirect('members:lesson_edit', pk=lesson.pk)
    else:
        form = LessonForm(instance=lesson)

    # テスト情報
    quiz = None
    if hasattr(lesson, 'quiz'):
        quiz = lesson.quiz

    return render(request, 'members/lesson_edit.html', {
        'form': form,
        'course': course,
        'site': site,
        'lesson': lesson,
        'quiz': quiz,
        'is_new': False,
    })


@login_required
@project_permission_required('can_manage_members')
def lesson_delete_view(request, pk):
    """レッスン削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    lesson = get_object_or_404(Lesson, pk=pk, course__site__project=project)
    course = lesson.course

    if request.method == 'POST':
        lesson_title = lesson.title
        lesson.delete()
        messages.success(request, f'レッスン「{lesson_title}」を削除しました。')
        return redirect('members:course_edit', pk=course.pk)

    return render(request, 'members/lesson_delete_confirm.html', {
        'lesson': lesson,
        'course': course,
    })


@login_required
@project_permission_required('can_manage_members')
def quiz_setup_view(request, pk):
    """テスト設定（任意のレッスンに紐付くテストを設定）"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    lesson = get_object_or_404(Lesson, pk=pk, course__site__project=project)
    course = lesson.course
    site = course.site

    quiz, created = Quiz.objects.get_or_create(lesson=lesson)

    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'テスト設定を更新しました。')
            return redirect('members:quiz_setup', pk=lesson.pk)
    else:
        form = QuizForm(instance=quiz)

    questions = quiz.questions.all()

    return render(request, 'members/quiz_setup.html', {
        'form': form,
        'quiz': quiz,
        'lesson': lesson,
        'course': course,
        'site': site,
        'questions': questions,
    })


@login_required
@project_permission_required('can_manage_members')
def question_create_view(request, pk):
    """問題作成"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    quiz = get_object_or_404(Quiz, pk=pk, lesson__course__site__project=project)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        formset = ChoiceFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            # 自動で表示順をセット
            max_order = quiz.questions.count()
            question.sort_order = max_order
            question.save()
            formset.instance = question
            formset.save()
            messages.success(request, '問題を追加しました。')
            return redirect('members:quiz_setup', pk=quiz.lesson.pk)
    else:
        form = QuestionForm()
        formset = ChoiceFormSet()

    lesson = quiz.lesson
    course = lesson.course
    site = course.site

    return render(request, 'members/question_edit.html', {
        'form': form,
        'formset': formset,
        'quiz': quiz,
        'lesson': lesson,
        'course': course,
        'site': site,
        'is_new': True,
    })


@login_required
@project_permission_required('can_manage_members')
def question_edit_view(request, pk):
    """問題編集"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    question = get_object_or_404(Question, pk=pk, quiz__lesson__course__site__project=project)
    quiz = question.quiz
    lesson = quiz.lesson
    course = lesson.course
    site = course.site

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, '問題を更新しました。')
            return redirect('members:quiz_setup', pk=lesson.pk)
    else:
        form = QuestionForm(instance=question)
        formset = ChoiceFormSet(instance=question)

    return render(request, 'members/question_edit.html', {
        'form': form,
        'formset': formset,
        'quiz': quiz,
        'question': question,
        'lesson': lesson,
        'course': course,
        'site': site,
        'is_new': False,
    })


@login_required
@project_permission_required('can_manage_members')
def question_delete_view(request, pk):
    """問題削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    question = get_object_or_404(Question, pk=pk, quiz__lesson__course__site__project=project)
    lesson = question.quiz.lesson

    if request.method == 'POST':
        question.delete()
        messages.success(request, '問題を削除しました。')
        return redirect('members:quiz_setup', pk=lesson.pk)

    return render(request, 'members/question_delete_confirm.html', {
        'question': question,
        'lesson': lesson,
    })


@login_required
@project_permission_required('can_manage_members')
def quiz_delete_view(request, pk):
    """テスト削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    lesson = get_object_or_404(Lesson, pk=pk, course__site__project=project)

    if request.method == 'POST' and hasattr(lesson, 'quiz'):
        lesson.quiz.delete()
        messages.success(request, 'テストを削除しました。')

    return redirect('members:lesson_edit', pk=lesson.pk)


@login_required
@project_permission_required('can_manage_members')
def certificate_edit_view(request, pk):
    """証書設定"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    course = get_object_or_404(Course, pk=pk, site__project=project)
    site = course.site

    certificate, created = Certificate.objects.get_or_create(
        course=course,
        defaults={'title': f'{course.title} 修了証書', 'issuer_name': ''},
    )

    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES, instance=certificate)
        if form.is_valid():
            form.save()
            messages.success(request, '証書設定を更新しました。')
            return redirect('members:certificate_edit', pk=course.pk)
    else:
        form = CertificateForm(instance=certificate)

    return render(request, 'members/certificate_edit.html', {
        'form': form,
        'certificate': certificate,
        'course': course,
        'site': site,
    })


@login_required
@project_permission_required('can_manage_members')
def quiz_attempts_view(request, pk):
    """受験結果一覧"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    quiz = get_object_or_404(Quiz, pk=pk, lesson__course__site__project=project)
    lesson = quiz.lesson
    course = lesson.course
    site = course.site

    attempts = quiz.attempts.select_related('enrollment__contact').all()

    return render(request, 'members/quiz_attempts.html', {
        'quiz': quiz,
        'lesson': lesson,
        'course': course,
        'site': site,
        'attempts': attempts,
    })


@login_required
@project_permission_required('can_manage_members')
def lesson_preview_view(request, pk):
    """レッスンプレビュー（JSON API）"""
    project = getattr(request, 'current_project', None)
    if not project:
        return JsonResponse({'error': 'No project'}, status=403)

    lesson = get_object_or_404(Lesson, pk=pk, course__site__project=project)

    data = {
        'title': lesson.title,
        'content_type': lesson.get_content_type_display(),
        'body': lesson.body,
        'sort_order': lesson.sort_order,
        'is_published': lesson.is_published,
        'quiz': None,
    }

    if hasattr(lesson, 'quiz'):
        quiz = lesson.quiz
        questions = []
        for q in quiz.questions.prefetch_related('choices').all():
            questions.append({
                'text': q.text,
                'explanation': q.explanation,
                'choices': [
                    {'text': c.text, 'is_correct': c.is_correct}
                    for c in q.choices.all()
                ],
            })
        data['quiz'] = {
            'description': quiz.description,
            'passing_score': quiz.passing_score,
            'question_count': quiz.questions.count(),
            'questions': questions,
        }

    return JsonResponse(data)
