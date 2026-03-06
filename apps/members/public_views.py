from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from apps.contacts.models import Contact
from apps.members.forms import MemberLoginForm
from apps.members.models import (
    MemberSite, Course, Lesson, Enrollment, LessonProgress,
    Quiz, Question, Choice, QuizAttempt, QuizAnswer, Certificate, IssuedCertificate,
)
from apps.sysadmin.models import MemberSession, Inquiry

import random
import uuid


def _get_member_contact(request, site):
    """セッションから会員のContactを取得。未認証ならNone。セッション無効なら'session_expired'。"""
    contact_id = request.session.get('member_contact_id')
    site_id = request.session.get('member_site_id')
    if not contact_id or str(site_id) != str(site.pk):
        return None

    # Check single-session enforcement
    session_key = request.session.get('member_session_key')
    if session_key:
        active = MemberSession.objects.filter(
            contact_id=contact_id, site=site,
            session_key=session_key, is_active=True
        ).exists()
        if not active:
            # Session invalidated (logged in from another device)
            request.session.flush()
            return 'session_expired'

    try:
        return Contact.objects.get(pk=contact_id, project=site.project)
    except Contact.DoesNotExist:
        return None


def _check_quiz_gate(enrollment, lesson):
    """このレッスンより前にある未合格のゲートテストがあるかチェック。ブロック元のlessonを返す。"""
    gate_quizzes = Quiz.objects.filter(
        lesson__course=lesson.course,
        lesson__sort_order__lt=lesson.sort_order,
        is_gate=True,
    ).select_related('lesson')
    for quiz in gate_quizzes:
        if not QuizAttempt.objects.filter(quiz=quiz, enrollment=enrollment, passed=True).exists():
            return quiz.lesson
    return None


def _check_course_prerequisite(contact, course):
    """コースの前提テストが設定されていて未合格ならそのlessonを返す。"""
    if not course.prerequisite_quiz or not hasattr(course.prerequisite_quiz, 'quiz'):
        return None
    quiz = course.prerequisite_quiz.quiz
    if QuizAttempt.objects.filter(quiz=quiz, enrollment__contact=contact, passed=True).exists():
        return None
    return course.prerequisite_quiz


def _issue_certificate(enrollment, quiz):
    """合格時に卒業証書を発行する。"""
    course = quiz.lesson.course
    try:
        cert = course.certificate
    except Certificate.DoesNotExist:
        return None
    issued, created = IssuedCertificate.objects.get_or_create(
        certificate=cert, contact=enrollment.contact, enrollment=enrollment,
        defaults={'certificate_number': f'CERT-{uuid.uuid4().hex[:8].upper()}'}
    )
    return issued


def member_login_view(request, site_slug):
    """会員ログイン"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    error_message = ''

    if request.method == 'POST':
        form = MemberLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                contact = Contact.objects.get(email=email, project=site.project)
                if contact.password_hash and check_password(password, contact.password_hash):
                    # 認証成功 - 既存セッションを無効化
                    MemberSession.objects.filter(
                        contact=contact, site=site, is_active=True
                    ).update(is_active=False)
                    # セッションキーを確保
                    if not request.session.session_key:
                        request.session.create()
                    # 新規セッション作成
                    MemberSession.objects.create(
                        contact=contact,
                        site=site,
                        session_key=request.session.session_key,
                        ip_address=request.META.get('REMOTE_ADDR', ''),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                        is_active=True,
                    )
                    # セッションに情報を保存
                    request.session['member_contact_id'] = contact.id
                    request.session['member_site_id'] = site.id
                    request.session['member_session_key'] = request.session.session_key
                    return redirect('members_public:member_home', site_slug=site.slug)
                else:
                    error_message = 'メールアドレスまたはパスワードが正しくありません。'
            except Contact.DoesNotExist:
                error_message = 'メールアドレスまたはパスワードが正しくありません。'
    else:
        form = MemberLoginForm()

    return render(request, 'members/public/member_login.html', {
        'form': form,
        'site': site,
        'error_message': error_message,
    })


def member_logout_view(request, site_slug):
    """会員ログアウト"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    # MemberSessionを無効化
    contact_id = request.session.get('member_contact_id')
    if contact_id:
        MemberSession.objects.filter(
            contact_id=contact_id, site=site, is_active=True
        ).update(is_active=False)
    request.session.pop('member_contact_id', None)
    request.session.pop('member_site_id', None)
    return redirect('members_public:member_login', site_slug=site.slug)


def site_home_view(request, site_slug):
    """会員サイトトップ（コース一覧表示）"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        messages.error(request, '別のデバイスでログインされたため、セッションが無効になりました。')
        return redirect('members_public:member_login', site_slug=site.slug)
    if not contact:
        return redirect('members_public:member_login', site_slug=site.slug)

    # 受講中のコースを取得
    enrollments = Enrollment.objects.filter(
        contact=contact,
        course__site=site,
        course__is_published=True,
    ).select_related('course').prefetch_related('course__lessons', 'progress_records')

    # コースと進捗率を計算
    course_data = []
    for enrollment in enrollments:
        course = enrollment.course
        total_lessons = course.lessons.filter(is_published=True).count()
        completed_lessons = enrollment.progress_records.filter(is_completed=True).count()
        progress_percent = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0

        course_data.append({
            'course': course,
            'enrollment': enrollment,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percent': progress_percent,
        })

    # Overall progress
    all_enrollments = Enrollment.objects.filter(contact=contact, course__site=site)
    total_lessons = 0
    completed_lessons = 0
    for enrollment in all_enrollments:
        lessons = enrollment.course.lessons.filter(is_published=True)
        total_lessons += lessons.count()
        completed_lessons += LessonProgress.objects.filter(
            enrollment=enrollment, lesson__in=lessons, is_completed=True
        ).count()
    overall_progress = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0

    # Recent activity (last 5 accessed lessons)
    recent_progress = LessonProgress.objects.filter(
        enrollment__contact=contact, enrollment__course__site=site
    ).select_related('lesson', 'enrollment__course').order_by('-last_accessed_at')[:5]

    # Quiz results summary
    quiz_attempts = QuizAttempt.objects.filter(
        enrollment__contact=contact, enrollment__course__site=site
    ).select_related('quiz__lesson')
    best_scores = {}
    for attempt in quiz_attempts:
        key = attempt.quiz_id
        if key not in best_scores or attempt.percentage > best_scores[key]['percentage']:
            best_scores[key] = {
                'quiz_name': attempt.quiz.lesson.title,
                'percentage': attempt.percentage,
                'passed': attempt.passed,
            }

    # Certificates
    certificates = IssuedCertificate.objects.filter(
        contact=contact, enrollment__course__site=site
    ).select_related('certificate__course')

    return render(request, 'members/public/site_home.html', {
        'site': site,
        'contact': contact,
        'course_data': course_data,
        'overall_progress': overall_progress,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'recent_progress': recent_progress,
        'best_scores': best_scores,
        'certificates': certificates,
    })


def course_detail_view(request, site_slug, course_slug):
    """コース詳細（レッスン一覧 + 進捗表示）"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        messages.error(request, '別のデバイスでログインされたため、セッションが無効になりました。')
        return redirect('members_public:member_login', site_slug=site.slug)
    if not contact:
        return redirect('members_public:member_login', site_slug=site.slug)

    course = get_object_or_404(Course, slug=course_slug, site=site, is_published=True)

    # Enrollment チェック
    try:
        enrollment = Enrollment.objects.get(contact=contact, course=course)
    except Enrollment.DoesNotExist:
        return render(request, 'members/public/course_detail.html', {
            'site': site,
            'contact': contact,
            'course': course,
            'has_access': False,
        })

    # 前提テストチェック
    prereq_lesson = _check_course_prerequisite(contact, course)
    if prereq_lesson:
        return render(request, 'members/public/course_detail.html', {
            'site': site,
            'contact': contact,
            'course': course,
            'has_access': True,
            'enrollment': enrollment,
            'prerequisite_blocked': True,
            'prereq_lesson': prereq_lesson,
        })

    lessons = course.lessons.filter(is_published=True).select_related('quiz')
    total_lessons = lessons.count()

    # 各レッスンの完了状態を取得
    completed_lesson_ids = set(
        LessonProgress.objects.filter(
            enrollment=enrollment,
            is_completed=True,
        ).values_list('lesson_id', flat=True)
    )

    lesson_data = []
    for idx, lesson in enumerate(lessons, 1):
        lesson_data.append({
            'lesson': lesson,
            'number': idx,
            'is_completed': lesson.id in completed_lesson_ids,
        })

    # テスト・ゲート状態を各レッスンに追加
    for item in lesson_data:
        les = item['lesson']
        item['is_gated'] = False
        item['quiz_passed'] = None
        item['has_quiz'] = hasattr(les, 'quiz')
        if item['has_quiz']:
            best = QuizAttempt.objects.filter(
                quiz=les.quiz, enrollment=enrollment, passed=True
            ).first()
            item['quiz_passed'] = best is not None
        # ゲートチェック
        gate = _check_quiz_gate(enrollment, les)
        if gate:
            item['is_gated'] = True

    completed_count = len(completed_lesson_ids)
    progress_percent = int((completed_count / total_lessons * 100)) if total_lessons > 0 else 0

    return render(request, 'members/public/course_detail.html', {
        'site': site,
        'contact': contact,
        'course': course,
        'has_access': True,
        'enrollment': enrollment,
        'lesson_data': lesson_data,
        'total_lessons': total_lessons,
        'completed_count': completed_count,
        'progress_percent': progress_percent,
    })


def lesson_view(request, site_slug, lesson_slug):
    """レッスン閲覧"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        messages.error(request, '別のデバイスでログインされたため、セッションが無効になりました。')
        return redirect('members_public:member_login', site_slug=site.slug)
    if not contact:
        return redirect('members_public:member_login', site_slug=site.slug)

    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course__site=site,
        is_published=True,
    )
    course = lesson.course

    # Enrollment チェック
    try:
        enrollment = Enrollment.objects.get(contact=contact, course=course)
    except Enrollment.DoesNotExist:
        if not lesson.is_preview:
            return redirect('members_public:member_course', site_slug=site.slug, course_slug=course.slug)
        enrollment = None

    # ゲートチェック
    if enrollment:
        gate_lesson = _check_quiz_gate(enrollment, lesson)
        if gate_lesson:
            return render(request, 'members/public/lesson_gated.html', {
                'site': site, 'contact': contact, 'course': course,
                'lesson': lesson, 'gate_lesson': gate_lesson,
            })

    # LessonProgress の更新/作成
    progress = None
    if enrollment:
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
        )
        # last_accessed_at は auto_now なので save するだけでOK
        if not created:
            progress.save()

    # 前後のレッスン
    published_lessons = list(course.lessons.filter(is_published=True))
    current_index = None
    for idx, l in enumerate(published_lessons):
        if l.id == lesson.id:
            current_index = idx
            break

    prev_lesson = published_lessons[current_index - 1] if current_index and current_index > 0 else None
    next_lesson = published_lessons[current_index + 1] if current_index is not None and current_index < len(published_lessons) - 1 else None

    # テスト情報
    quiz = getattr(lesson, 'quiz', None)
    quiz_attempt = None
    if quiz and enrollment:
        quiz_attempt = QuizAttempt.objects.filter(
            quiz=quiz, enrollment=enrollment
        ).order_by('-started_at').first()

    return render(request, 'members/public/lesson_view.html', {
        'site': site,
        'contact': contact,
        'course': course,
        'lesson': lesson,
        'progress': progress,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'quiz': quiz,
        'quiz_attempt': quiz_attempt,
    })


def lesson_complete_view(request, site_slug, lesson_slug):
    """レッスン完了マーク（POST）"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        return JsonResponse({'error': 'Session expired'}, status=401)
    if not contact:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course__site=site,
        is_published=True,
    )

    try:
        enrollment = Enrollment.objects.get(contact=contact, course=lesson.course)
    except Enrollment.DoesNotExist:
        return JsonResponse({'error': 'Not enrolled'}, status=403)

    progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson,
    )
    progress.is_completed = True
    progress.completed_at = timezone.now()
    progress.save()

    # HTMX対応: HTMLフラグメントを返す
    if request.headers.get('HX-Request'):
        return render(request, 'members/public/_lesson_complete_button.html', {
            'progress': progress,
            'site': site,
            'lesson': lesson,
        })

    return redirect('members_public:member_lesson', site_slug=site.slug, lesson_slug=lesson.slug)


def quiz_start_view(request, site_slug, lesson_slug):
    """テスト開始画面（問題表示 + 回答フォーム）"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        messages.error(request, '別のデバイスでログインされたため、セッションが無効になりました。')
        return redirect('members_public:member_login', site_slug=site.slug)
    if not contact:
        return redirect('members_public:member_login', site_slug=site.slug)

    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course__site=site,
        is_published=True,
    )
    course = lesson.course

    try:
        enrollment = Enrollment.objects.get(contact=contact, course=course)
    except Enrollment.DoesNotExist:
        return redirect('members_public:member_course', site_slug=site.slug, course_slug=course.slug)

    quiz = get_object_or_404(Quiz, lesson=lesson)

    # 受験履歴
    attempts_list = QuizAttempt.objects.filter(quiz=quiz, enrollment=enrollment).order_by('-started_at')
    attempt_count = attempts_list.count()

    # 受験可能かチェック
    can_attempt = True
    if quiz.max_attempts > 0 and attempt_count >= quiz.max_attempts:
        can_attempt = False

    # 最高スコアの合格記録
    best_attempt = QuizAttempt.objects.filter(
        quiz=quiz, enrollment=enrollment, passed=True
    ).order_by('-percentage').first()

    # 問題を取得
    questions = list(quiz.questions.prefetch_related('choices').all())
    if quiz.shuffle_questions:
        random.shuffle(questions)
    # 選択肢のシャッフル
    for q in questions:
        choices_list = list(q.choices.all())
        if quiz.shuffle_choices:
            random.shuffle(choices_list)
        q.shuffled_choices = choices_list

    return render(request, 'members/public/quiz_start.html', {
        'site': site,
        'contact': contact,
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
        'questions': questions,
        'attempt_count': attempt_count,
        'can_attempt': can_attempt,
        'best_attempt': best_attempt,
        'attempts_list': attempts_list,
    })


def quiz_submit_view(request, site_slug, lesson_slug):
    """テスト回答提出（POST のみ）"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        messages.error(request, '別のデバイスでログインされたため、セッションが無効になりました。')
        return redirect('members_public:member_login', site_slug=site.slug)
    if not contact:
        return redirect('members_public:member_login', site_slug=site.slug)

    if request.method != 'POST':
        return redirect('members_public:quiz_start', site_slug=site.slug, lesson_slug=lesson_slug)

    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course__site=site,
        is_published=True,
    )
    course = lesson.course

    try:
        enrollment = Enrollment.objects.get(contact=contact, course=course)
    except Enrollment.DoesNotExist:
        return redirect('members_public:member_course', site_slug=site.slug, course_slug=course.slug)

    quiz = get_object_or_404(Quiz, lesson=lesson)

    # 受験回数チェック
    attempt_count = QuizAttempt.objects.filter(quiz=quiz, enrollment=enrollment).count()
    if quiz.max_attempts > 0 and attempt_count >= quiz.max_attempts:
        return redirect('members_public:quiz_start', site_slug=site.slug, lesson_slug=lesson.slug)

    # QuizAttemptを作成
    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        enrollment=enrollment,
        score=0,
        max_score=0,
        percentage=0,
        passed=False,
    )

    # 問題を取得して採点
    questions = quiz.questions.prefetch_related('choices').all()
    total_score = 0
    max_score = 0

    for question in questions:
        max_score += question.points
        correct_choice_ids = set(
            question.choices.filter(is_correct=True).values_list('id', flat=True)
        )

        # ユーザーの回答を取得
        if question.question_type in ('single', 'true_false'):
            selected_id = request.POST.get(f'question_{question.id}')
            selected_ids = {int(selected_id)} if selected_id else set()
        else:  # multiple
            selected_vals = request.POST.getlist(f'question_{question.id}')
            selected_ids = {int(v) for v in selected_vals if v}

        # 正誤判定
        if question.question_type in ('single', 'true_false'):
            is_correct = selected_ids == correct_choice_ids
        else:  # multiple
            is_correct = selected_ids == correct_choice_ids

        if is_correct:
            total_score += question.points

        # QuizAnswerを作成
        answer = QuizAnswer.objects.create(
            attempt=attempt,
            question=question,
            is_correct=is_correct,
        )
        if selected_ids:
            answer.selected_choices.set(Choice.objects.filter(id__in=selected_ids))

    # スコア計算
    percentage = int((total_score / max_score * 100)) if max_score > 0 else 0
    passed = percentage >= quiz.passing_score

    attempt.score = total_score
    attempt.max_score = max_score
    attempt.percentage = percentage
    attempt.passed = passed
    attempt.completed_at = timezone.now()
    attempt.save()

    # 合格時の処理
    if passed:
        # LessonProgressを完了にする
        progress, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
        )
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save()

        # 最終テストなら証書を発行
        if quiz.is_final_test:
            _issue_certificate(enrollment, quiz)

    return redirect('members_public:quiz_result',
                    site_slug=site.slug,
                    lesson_slug=lesson.slug,
                    attempt_id=attempt.id)


def quiz_result_view(request, site_slug, lesson_slug, attempt_id):
    """テスト結果表示"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        messages.error(request, '別のデバイスでログインされたため、セッションが無効になりました。')
        return redirect('members_public:member_login', site_slug=site.slug)
    if not contact:
        return redirect('members_public:member_login', site_slug=site.slug)

    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course__site=site,
        is_published=True,
    )
    course = lesson.course

    try:
        enrollment = Enrollment.objects.get(contact=contact, course=course)
    except Enrollment.DoesNotExist:
        return redirect('members_public:member_course', site_slug=site.slug, course_slug=course.slug)

    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        quiz__lesson=lesson,
        enrollment=enrollment,
    )
    quiz = attempt.quiz

    # 結果データを構築
    result_data = []
    answers = attempt.answers.select_related('question').prefetch_related(
        'selected_choices', 'question__choices'
    ).order_by('question__sort_order')

    for answer in answers:
        question = answer.question
        selected_ids = set(answer.selected_choices.values_list('id', flat=True))
        correct_ids = set(question.choices.filter(is_correct=True).values_list('id', flat=True))

        choices_data = []
        for choice in question.choices.all():
            choices_data.append({
                'choice': choice,
                'is_selected': choice.id in selected_ids,
                'is_correct': choice.is_correct,
            })

        result_data.append({
            'question': question,
            'answer': answer,
            'is_correct': answer.is_correct,
            'choices_data': choices_data,
        })

    # 証書チェック（合格かつ最終テストの場合）
    certificate_issued = None
    if attempt.passed and quiz.is_final_test:
        certificate_issued = IssuedCertificate.objects.filter(
            enrollment=enrollment,
            certificate__course=course,
        ).first()

    # 残り受験回数
    attempt_count = QuizAttempt.objects.filter(quiz=quiz, enrollment=enrollment).count()
    can_retry = True
    if quiz.max_attempts > 0 and attempt_count >= quiz.max_attempts:
        can_retry = False

    return render(request, 'members/public/quiz_result.html', {
        'site': site,
        'contact': contact,
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
        'attempt': attempt,
        'result_data': result_data,
        'certificate_issued': certificate_issued,
        'can_retry': can_retry,
        'attempt_count': attempt_count,
    })


def certificate_view(request, site_slug, cert_number):
    """卒業証書の公開表示ページ（認証不要）"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    issued = get_object_or_404(
        IssuedCertificate,
        certificate_number=cert_number,
        certificate__course__site=site,
    )
    certificate = issued.certificate
    contact = issued.contact
    course = certificate.course

    return render(request, 'members/public/certificate_view.html', {
        'site': site,
        'issued': issued,
        'certificate': certificate,
        'contact': contact,
        'course': course,
    })


def member_profile_view(request, site_slug):
    """会員プロフィール表示・更新"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        messages.error(request, '別のデバイスでログインされたため、セッションが無効になりました。')
        return redirect('members_public:member_login', site_slug=site.slug)
    if not contact:
        return redirect('members_public:member_login', site_slug=site.slug)

    success_message = ''
    error_message = ''

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not email:
            error_message = 'メールアドレスは必須です。'
        elif email != contact.email:
            # メールアドレスの一意性チェック
            if Contact.objects.filter(email=email, project=site.project).exclude(pk=contact.pk).exists():
                error_message = 'このメールアドレスは既に使用されています。'
            else:
                contact.name = name
                contact.email = email
                contact.phone = phone
                contact.save()
                success_message = 'プロフィールを更新しました。'
        else:
            contact.name = name
            contact.phone = phone
            contact.save()
            success_message = 'プロフィールを更新しました。'

    return render(request, 'members/public/profile.html', {
        'site': site,
        'contact': contact,
        'success_message': success_message,
        'error_message': error_message,
    })


def member_password_change_view(request, site_slug):
    """会員パスワード変更"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        messages.error(request, '別のデバイスでログインされたため、セッションが無効になりました。')
        return redirect('members_public:member_login', site_slug=site.slug)
    if not contact:
        return redirect('members_public:member_login', site_slug=site.slug)

    success_message = ''
    error_message = ''

    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not current_password or not new_password or not confirm_password:
            error_message = 'すべての項目を入力してください。'
        elif not check_password(current_password, contact.password_hash):
            error_message = '現在のパスワードが正しくありません。'
        elif len(new_password) < 8:
            error_message = '新しいパスワードは8文字以上にしてください。'
        elif new_password != confirm_password:
            error_message = '新しいパスワードが一致しません。'
        else:
            contact.password_hash = make_password(new_password)
            contact.save()
            success_message = 'パスワードを変更しました。'

    return render(request, 'members/public/password_change.html', {
        'site': site,
        'contact': contact,
        'success_message': success_message,
        'error_message': error_message,
    })


def member_inquiry_view(request, site_slug):
    """会員お問い合わせ送信"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        messages.error(request, '別のデバイスでログインされたため、セッションが無効になりました。')
        return redirect('members_public:member_login', site_slug=site.slug)
    if not contact:
        return redirect('members_public:member_login', site_slug=site.slug)

    error_message = ''

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()

        if not subject or not body:
            error_message = '件名と内容を入力してください。'
        else:
            Inquiry.objects.create(
                contact=contact,
                site=site,
                subject=subject,
                body=body,
            )
            return redirect('members_public:member_inquiry_history', site_slug=site.slug)

    return render(request, 'members/public/inquiry_form.html', {
        'site': site,
        'contact': contact,
        'error_message': error_message,
    })


def member_inquiry_history_view(request, site_slug):
    """会員お問い合わせ履歴"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        messages.error(request, '別のデバイスでログインされたため、セッションが無効になりました。')
        return redirect('members_public:member_login', site_slug=site.slug)
    if not contact:
        return redirect('members_public:member_login', site_slug=site.slug)

    inquiries = Inquiry.objects.filter(contact=contact, site=site).order_by('-created_at')

    return render(request, 'members/public/inquiry_history.html', {
        'site': site,
        'contact': contact,
        'inquiries': inquiries,
    })


def member_manual_view(request, site_slug):
    """受講生マニュアル"""
    site = get_object_or_404(MemberSite, slug=site_slug, is_active=True)
    contact = _get_member_contact(request, site)
    if contact == 'session_expired':
        messages.error(request, '別のデバイスでログインされたため、セッションが無効になりました。')
        return redirect('members_public:member_login', site_slug=site.slug)
    if not contact:
        return redirect('members_public:member_login', site_slug=site.slug)
    return render(request, 'members/public/manual.html', {
        'site': site,
        'contact': contact,
    })
