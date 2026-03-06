from django.db import models


class MemberSite(models.Model):
    project = models.ForeignKey('accounts.Project', on_delete=models.CASCADE, related_name='member_sites')
    name = models.CharField('サイト名', max_length=200)
    slug = models.SlugField('スラッグ', unique=True)
    description = models.TextField('説明', blank=True)
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'member_sites'

    def __str__(self):
        return self.name


class Course(models.Model):
    site = models.ForeignKey(MemberSite, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField('コースタイトル', max_length=200)
    slug = models.SlugField('スラッグ')
    description = models.TextField('説明', blank=True)
    thumbnail = models.ImageField('サムネイル', upload_to='courses/', blank=True)
    sort_order = models.IntegerField('表示順', default=0)
    is_published = models.BooleanField('公開', default=False)
    prerequisite_quiz = models.ForeignKey(
        'Lesson', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='gated_courses', verbose_name='前提テスト',
        help_text='このテストに合格しないとコースにアクセスできません',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses'
        ordering = ['sort_order']

    def __str__(self):
        return self.title


class Lesson(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('video', '動画'),
        ('text', 'テキスト'),
        ('pdf', 'PDF'),
        ('quiz', 'テスト'),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField('レッスンタイトル', max_length=200)
    slug = models.SlugField('スラッグ')
    content_type = models.CharField('コンテンツタイプ', max_length=10, choices=CONTENT_TYPE_CHOICES, default='text')
    body = models.TextField('本文(HTML)', blank=True)
    video_url = models.URLField('動画URL', blank=True)
    file = models.FileField('ファイル', upload_to='lessons/', blank=True)
    sort_order = models.IntegerField('表示順', default=0)
    is_published = models.BooleanField('公開', default=False)
    is_preview = models.BooleanField('プレビュー可能', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lessons'
        ordering = ['sort_order']

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField('有効期限', null=True, blank=True)
    order = models.ForeignKey('products.Order', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'enrollments'
        unique_together = [('contact', 'course')]

    def __str__(self):
        return f'{self.contact} - {self.course}'


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='progress_records')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
    is_completed = models.BooleanField('完了', default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lesson_progress'
        unique_together = [('enrollment', 'lesson')]

    def __str__(self):
        return f'{self.enrollment} - {self.lesson}'


# --- テスト・クイズ ---

class Quiz(models.Model):
    """テスト設定（Lesson 1:1）"""
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    description = models.TextField('テスト説明', blank=True)
    passing_score = models.IntegerField('合格ライン(%)', default=70)
    time_limit_minutes = models.IntegerField('制限時間(分)', null=True, blank=True)
    max_attempts = models.IntegerField('最大受験回数', default=0, help_text='0=無制限')
    shuffle_questions = models.BooleanField('問題順ランダム', default=False)
    shuffle_choices = models.BooleanField('選択肢ランダム', default=False)
    is_gate = models.BooleanField('ゲート', default=False, help_text='合格しないと次のレッスンに進めない')
    is_final_test = models.BooleanField('最終テスト', default=False, help_text='合格で卒業証書を発行')
    show_correct_answers = models.BooleanField('正解を表示', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'quizzes'

    def __str__(self):
        return f'テスト: {self.lesson.title}'


class Question(models.Model):
    """テストの問題"""
    QUESTION_TYPES = [
        ('true_false', '○×式'),
        ('single', '択一式'),
        ('multiple', '複数選択式'),
    ]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField('問題タイプ', max_length=20, choices=QUESTION_TYPES, default='single')
    text = models.TextField('問題文')
    explanation = models.TextField('解説', blank=True)
    points = models.IntegerField('配点', default=1)
    sort_order = models.IntegerField('表示順', default=0)

    class Meta:
        db_table = 'quiz_questions'
        ordering = ['sort_order']

    def __str__(self):
        return f'Q{self.sort_order}: {self.text[:50]}'


class Choice(models.Model):
    """問題の選択肢"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField('選択肢テキスト', max_length=500)
    is_correct = models.BooleanField('正解', default=False)
    sort_order = models.IntegerField('表示順', default=0)

    class Meta:
        db_table = 'quiz_choices'
        ordering = ['sort_order']

    def __str__(self):
        return self.text[:50]


class QuizAttempt(models.Model):
    """テスト受験記録"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.IntegerField('得点', default=0)
    max_score = models.IntegerField('満点', default=0)
    percentage = models.IntegerField('正解率(%)', default=0)
    passed = models.BooleanField('合格', default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField('完了日時', null=True, blank=True)

    class Meta:
        db_table = 'quiz_attempts'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.enrollment.contact} - {self.quiz} ({self.percentage}%)'


class QuizAnswer(models.Model):
    """各問題への回答"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_correct = models.BooleanField('正解', default=False)
    selected_choices = models.ManyToManyField(Choice, blank=True, related_name='quiz_answers')

    class Meta:
        db_table = 'quiz_answers'

    def __str__(self):
        return f'{self.question} - {"○" if self.is_correct else "×"}'


# --- 卒業証書 ---

class Certificate(models.Model):
    """卒業証書テンプレート"""
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='certificate')
    title = models.CharField('証書タイトル', max_length=200)
    description = models.TextField('メッセージ', blank=True)
    issuer_name = models.CharField('発行者名', max_length=200)
    template_image = models.ImageField('背景画像', upload_to='certificates/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'certificates'

    def __str__(self):
        return f'証書: {self.title}'


class IssuedCertificate(models.Model):
    """発行済み卒業証書"""
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE, related_name='issued')
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='certificates')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='certificates')
    certificate_number = models.CharField('証書番号', max_length=50, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'issued_certificates'

    def __str__(self):
        return f'{self.certificate_number} - {self.contact}'
