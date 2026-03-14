"""
ライブコマーサー育成講座 コンテンツ一括登録コマンド

MemberSite配下にCourse×3、Lesson×40、Quiz×40、Question×200、Choice×800を一括作成する。
冪等: 同じslugが既に存在する場合はスキップする。

Usage:
    python manage.py populate_course_content --project-id=1
"""
import json
import os
import random
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Project
from apps.members.models import (
    MemberSite, Course, Lesson, Quiz, Question, Choice, Certificate,
)


class Command(BaseCommand):
    help = 'ライブコマーサー育成講座のコース・レッスン・クイズを一括セットアップ'

    def add_arguments(self, parser):
        parser.add_argument('--project-id', type=int, help='Project ID')

    def handle(self, *args, **options):
        project = self._get_project(options)
        self.stdout.write(f'Project: {project.name} (ID={project.id})')

        site = self._get_site()
        lesson_data = self._load_lesson_data()
        quiz_data = self._load_quiz_data()

        stage_lessons = {1: [], 2: [], 3: []}
        for ld in lesson_data:
            stage_lessons[ld['stage']].append(ld)

        courses = {}
        final_test_lessons = {}

        for stage_num, stage_def in STAGE_DEFS.items():
            course = self._create_course(site, stage_def, stage_num)
            courses[stage_num] = course

            lessons = stage_lessons.get(stage_num, [])
            for ld in lessons:
                lesson = self._create_lesson(course, ld)
                self._create_quiz(lesson, quiz_data.get(str(ld['num']), []), ld)

            # 最終テスト用レッスン
            final_lesson = self._create_final_test_lesson(course, stage_def, stage_num, lessons)
            final_test_lessons[stage_num] = final_lesson

            # Certificate
            self._create_certificate(course, stage_def)

        # prerequisite_quiz 設定
        self._set_prerequisites(courses, final_test_lessons)

        self.stdout.write(self.style.SUCCESS('コンテンツ登録完了'))

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _get_project(self, options):
        pid = options.get('project_id')
        if pid:
            try:
                return Project.objects.get(id=pid)
            except Project.DoesNotExist:
                raise CommandError(f'Project ID={pid} が見つかりません')
        project = Project.objects.first()
        if not project:
            raise CommandError('Projectが1つもありません。先にProjectを作成してください。')
        return project

    def _get_site(self):
        try:
            return MemberSite.objects.get(slug='live-commercer-course')
        except MemberSite.DoesNotExist:
            raise CommandError(
                'MemberSite(slug=live-commercer-course)が見つかりません。'
                '先に setup_live_commercer_course を実行してください。'
            )

    def _load_lesson_data(self):
        path = Path(__file__).resolve().parent.parent.parent.parent.parent / 'lesson_data_full.json'
        if not path.exists():
            raise CommandError(f'lesson_data_full.json が見つかりません: {path}')
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_quiz_data(self):
        path = Path(__file__).resolve().parent.parent.parent.parent.parent / 'quiz_data.json'
        if not path.exists():
            raise CommandError(f'quiz_data.json が見つかりません: {path}')
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # Course
    # ------------------------------------------------------------------

    def _create_course(self, site, stage_def, stage_num):
        course, created = Course.objects.get_or_create(
            site=site,
            slug=stage_def['slug'],
            defaults={
                'title': stage_def['title'],
                'description': stage_def['description'],
                'sort_order': stage_num,
                'is_published': True,
            },
        )
        self.stdout.write(f'  Course: {"作成" if created else "既存"} - {course.title}')
        return course

    # ------------------------------------------------------------------
    # Lesson
    # ------------------------------------------------------------------

    def _create_lesson(self, course, ld):
        slug = f'v{ld["num"]:02d}'
        lesson, created = Lesson.objects.get_or_create(
            course=course,
            slug=slug,
            defaults={
                'title': ld['title'],
                'content_type': 'text',
                'body': self._build_lesson_html(ld),
                'sort_order': ld['num'],
                'is_published': True,
                'is_preview': ld['num'] in (1, 13, 29),  # 各STAGE最初のレッスンはプレビュー可
            },
        )
        if created:
            self.stdout.write(f'    Lesson: 作成 - {lesson.title}')
        return lesson

    def _build_lesson_html(self, ld):
        title_short = ld['title'].split('\uff5c')[1] if '\uff5c' in ld['title'] else ld['title']
        goal = ld.get('goal', '')
        kpi = ld.get('kpi', '')
        narration = ld.get('narration', '')
        telops = ld.get('telops', [])
        drill = ld.get('drill', '')

        # Convert narration to HTML paragraphs
        narr_parts = []
        for p in narration.strip().split('\n\n'):
            p = p.strip()
            if not p:
                continue
            lines = p.split('\n')
            narr_parts.append('<p>' + '<br>\n'.join(l.strip() for l in lines if l.strip()) + '</p>')
        narr_html = '\n'.join(narr_parts)

        telop_items = '\n'.join(f'<li>{t}</li>' for t in telops)

        return f"""<div class="lesson-content">
<h2>{title_short}</h2>

<div class="learning-goal" style="background:#f0f9ff;border-left:4px solid #3b82f6;padding:16px;margin:16px 0;border-radius:8px;">
<h3 style="margin-top:0;color:#1e40af;">学習目標</h3>
<p>{goal}</p>
<p><strong>KPI目安：</strong>{kpi}</p>
</div>

<div class="narration">
<h3>講義内容</h3>
{narr_html}
</div>

<div class="telop-list" style="background:#f8fafc;padding:16px;margin:16px 0;border-radius:8px;">
<h3>キーポイント</h3>
<ul>
{telop_items}
</ul>
</div>

<div class="mini-drill" style="background:#fef3c7;border-left:4px solid #f59e0b;padding:16px;margin:16px 0;border-radius:8px;">
<h3 style="margin-top:0;color:#92400e;">ミニドリル</h3>
<p><strong>{drill}</strong></p>
<p>録画またはメモに残して、次の動画やワークショップで相互チェックに使います。</p>
</div>
</div>"""

    # ------------------------------------------------------------------
    # Final Test Lesson
    # ------------------------------------------------------------------

    def _create_final_test_lesson(self, course, stage_def, stage_num, lessons):
        slug = f'stage{stage_num}-final-test'
        lesson, created = Lesson.objects.get_or_create(
            course=course,
            slug=slug,
            defaults={
                'title': stage_def['final_test_title'],
                'content_type': 'quiz',
                'body': f'<p>{stage_def["title"]}の最終認定テストです。全レッスンの内容から出題されます。合格ラインは80%です。</p>',
                'sort_order': 999,
                'is_published': True,
            },
        )
        if created:
            self.stdout.write(f'    Final Test: 作成 - {lesson.title}')
            # Create quiz for final test - aggregate questions from all lessons in this stage
            quiz, _ = Quiz.objects.get_or_create(
                lesson=lesson,
                defaults={
                    'description': f'{stage_def["title"]}の最終認定テスト',
                    'passing_score': 80,
                    'max_attempts': 0,
                    'shuffle_questions': True,
                    'shuffle_choices': True,
                    'is_gate': True,
                    'is_final_test': True,
                    'show_correct_answers': True,
                },
            )
            # Add 10 questions from across the stage
            quiz_data = self._load_quiz_data()
            final_questions = []
            for ld in lessons:
                qs = quiz_data.get(str(ld['num']), [])
                if qs:
                    # Pick Q1 (conclusion) from each lesson
                    final_questions.append(qs[0])

            random.seed(stage_num * 1000)
            if len(final_questions) > 10:
                final_questions = random.sample(final_questions, 10)

            for idx, q_data in enumerate(final_questions):
                question, q_created = Question.objects.get_or_create(
                    quiz=quiz,
                    text=q_data['text'],
                    defaults={
                        'question_type': 'single',
                        'explanation': q_data.get('explanation', ''),
                        'points': 1,
                        'sort_order': idx + 1,
                    },
                )
                if q_created:
                    random.seed(stage_num * 1000 + idx)
                    choices = q_data['choices'][:]
                    random.shuffle(choices)
                    for ci, c_data in enumerate(choices):
                        Choice.objects.get_or_create(
                            question=question,
                            text=c_data['text'],
                            defaults={
                                'is_correct': c_data['is_correct'],
                                'sort_order': ci + 1,
                            },
                        )

        return lesson

    # ------------------------------------------------------------------
    # Quiz (per lesson)
    # ------------------------------------------------------------------

    def _create_quiz(self, lesson, questions_data, ld):
        if not questions_data:
            return

        quiz, created = Quiz.objects.get_or_create(
            lesson=lesson,
            defaults={
                'description': f'{lesson.title} セルフチェック',
                'passing_score': 70,
                'max_attempts': 0,
                'shuffle_questions': False,
                'shuffle_choices': True,
                'is_gate': False,
                'is_final_test': False,
                'show_correct_answers': True,
            },
        )
        if not created:
            return

        self.stdout.write(f'      Quiz: 作成 - {quiz.description}')

        for idx, q_data in enumerate(questions_data):
            question, q_created = Question.objects.get_or_create(
                quiz=quiz,
                text=q_data['text'],
                defaults={
                    'question_type': 'single',
                    'explanation': q_data.get('explanation', ''),
                    'points': 1,
                    'sort_order': idx + 1,
                },
            )
            if q_created:
                random.seed(ld['num'] * 100 + idx * 10)
                choices = q_data['choices'][:]
                random.shuffle(choices)
                for ci, c_data in enumerate(choices):
                    Choice.objects.get_or_create(
                        question=question,
                        text=c_data['text'],
                        defaults={
                            'is_correct': c_data['is_correct'],
                            'sort_order': ci + 1,
                        },
                    )

    # ------------------------------------------------------------------
    # Certificate
    # ------------------------------------------------------------------

    def _create_certificate(self, course, stage_def):
        cert, created = Certificate.objects.get_or_create(
            course=course,
            defaults={
                'title': stage_def['cert_title'],
                'description': stage_def['cert_description'],
                'issuer_name': 'ライブコマーサー育成講座 運営事務局',
            },
        )
        if created:
            self.stdout.write(f'    Certificate: 作成 - {cert.title}')

    # ------------------------------------------------------------------
    # Prerequisites
    # ------------------------------------------------------------------

    def _set_prerequisites(self, courses, final_test_lessons):
        # STAGE2 requires STAGE1 final test
        if 2 in courses and 1 in final_test_lessons:
            course2 = courses[2]
            if course2.prerequisite_quiz is None:
                course2.prerequisite_quiz = final_test_lessons[1]
                course2.save(update_fields=['prerequisite_quiz'])
                self.stdout.write('  prerequisite: STAGE2 ← STAGE1最終テスト')

        # STAGE3 requires STAGE2 final test
        if 3 in courses and 2 in final_test_lessons:
            course3 = courses[3]
            if course3.prerequisite_quiz is None:
                course3.prerequisite_quiz = final_test_lessons[2]
                course3.save(update_fields=['prerequisite_quiz'])
                self.stdout.write('  prerequisite: STAGE3 ← STAGE2最終テスト')


# ======================================================================
# STAGE DEFINITIONS
# ======================================================================

STAGE_DEFS = {
    1: {
        'title': 'STAGE1 基礎編',
        'slug': 'stage1-basics',
        'description': (
            'ライブコマースの基礎を学ぶ第1段階。'
            'ライバーの役割理解、配信環境構築、フック設計、コメント誘発、'
            '同時処理、リスク管理、安全チェックリストまでを習得します。'
            '目標KPI：滞在1分+／コメント率5%+／CVR1%+'
        ),
        'final_test_title': 'STAGE1 最終認定テスト',
        'cert_title': 'ライブコマーサー育成講座 初級認定証',
        'cert_description': 'STAGE1（基礎編）の全カリキュラムを修了し、最終認定テストに合格したことを証します。',
    },
    2: {
        'title': 'STAGE2 中級編',
        'slug': 'stage2-intermediate',
        'description': (
            '配信を伸ばすための中級スキルを学ぶ第2段階。'
            'アルゴリズム理解、滞在率設計、CTR最適化、3階層台本、'
            'ストーリーテリング、FAQ構築、データ分析、PDCAサイクルを習得します。'
            '目標KPI：滞在2分+／コメント率5%+／CVR2%+'
        ),
        'final_test_title': 'STAGE2 最終認定テスト',
        'cert_title': 'ライブコマーサー育成講座 中級認定証',
        'cert_description': 'STAGE2（中級編）の全カリキュラムを修了し、最終認定テストに合格したことを証します。',
    },
    3: {
        'title': 'STAGE3 上級編',
        'slug': 'stage3-advanced',
        'description': (
            'プロとして安定運用するための上級スキルを学ぶ第3段階。'
            '60分配信構成、配信品質管理、商品構成戦略、PL思考、'
            '収入最大化、チーム運営、事業拡張までを習得します。'
            '目標KPI：全項目B以上の総合評価'
        ),
        'final_test_title': 'STAGE3 最終認定テスト',
        'cert_title': 'ライブコマーサー育成講座 上級認定証',
        'cert_description': 'STAGE3（上級編）の全カリキュラムを修了し、最終認定テストに合格したことを証します。',
    },
}
