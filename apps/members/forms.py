from django import forms
from apps.members.models import MemberSite, Course, Lesson, Quiz, Question, Choice, Certificate


class MemberSiteForm(forms.ModelForm):
    class Meta:
        model = MemberSite
        fields = ['name', 'slug', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
                'placeholder': 'サイト名を入力',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
                'placeholder': '英数字とハイフンのみ',
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
                'rows': 3,
                'placeholder': 'サイトの説明を入力',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500',
            }),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'slug', 'description', 'thumbnail', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
                'placeholder': 'コースタイトルを入力',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
                'placeholder': '英数字とハイフンのみ',
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
                'rows': 3,
                'placeholder': 'コースの説明を入力',
            }),
            'thumbnail': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500',
            }),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'slug', 'content_type', 'body', 'video_url', 'file', 'is_published', 'is_preview']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
                'placeholder': 'レッスンタイトルを入力',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
                'placeholder': '英数字とハイフンのみ',
            }),
            'content_type': forms.Select(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
                'id': 'id_content_type',
            }),
            'body': forms.Textarea(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm font-mono',
                'rows': 15,
                'placeholder': 'HTML形式で本文を入力',
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
                'placeholder': 'https://www.youtube.com/embed/...',
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500',
            }),
            'is_preview': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # テストはレッスン内から別途作成するので、コンテンツタイプ選択肢から除外
        self.fields['content_type'].choices = [
            c for c in self.fields['content_type'].choices if c[0] != 'quiz'
        ]


class MemberLoginForm(forms.Form):
    email = forms.EmailField(
        label='メールアドレス',
        widget=forms.EmailInput(attrs={
            'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
            'placeholder': 'example@email.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='パスワード',
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm',
            'placeholder': 'パスワードを入力',
            'autocomplete': 'current-password',
        }),
    )


TW_INPUT = 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm'
TW_CHECKBOX = 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
TW_TEXTAREA = TW_INPUT
TW_SELECT = TW_INPUT


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'description', 'passing_score', 'time_limit_minutes', 'max_attempts',
            'shuffle_questions', 'shuffle_choices', 'is_gate', 'is_final_test', 'show_correct_answers',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3, 'placeholder': 'テストの説明（受験者に表示されます）'}),
            'passing_score': forms.NumberInput(attrs={'class': TW_INPUT, 'min': 0, 'max': 100}),
            'time_limit_minutes': forms.NumberInput(attrs={'class': TW_INPUT, 'min': 1, 'placeholder': '空欄=制限なし'}),
            'max_attempts': forms.NumberInput(attrs={'class': TW_INPUT, 'min': 0}),
            'shuffle_questions': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'shuffle_choices': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'is_gate': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'is_final_test': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'show_correct_answers': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_type', 'text', 'explanation', 'points']
        widgets = {
            'question_type': forms.Select(attrs={'class': TW_SELECT}),
            'text': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3, 'placeholder': '問題文を入力'}),
            'explanation': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 2, 'placeholder': '正解の解説（任意）'}),
            'points': forms.NumberInput(attrs={'class': TW_INPUT, 'min': 1}),
        }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': '選択肢を入力'}),
            'is_correct': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
        }


ChoiceFormSet = forms.inlineformset_factory(
    Question, Choice,
    form=ChoiceForm,
    extra=4,
    max_num=8,
    can_delete=True,
)


class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['title', 'description', 'issuer_name', 'template_image']
        widgets = {
            'title': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': '例: 修了証書'}),
            'description': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 4, 'placeholder': '証書に表示するメッセージ'}),
            'issuer_name': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': '例: 田中料理教室'}),
            'template_image': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
            }),
        }
