from django import forms
from apps.emails.models import Scenario, ScenarioStep, Campaign
from apps.contacts.models import Tag


class ScenarioForm(forms.ModelForm):
    class Meta:
        model = Scenario
        fields = ['name', 'sender_name', 'cta_url', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'シナリオ名を入力',
            }),
            'sender_name': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': '例：田中太郎、○○事務局',
            }),
            'cta_url': forms.URLInput(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'https://example.com/apply',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
        }


class ScenarioStepForm(forms.ModelForm):
    class Meta:
        model = ScenarioStep
        fields = ['step_number', 'delay_days', 'delay_hours', 'subject', 'body_html', 'body_text', 'is_active']
        widgets = {
            'step_number': forms.NumberInput(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'min': '1',
            }),
            'delay_days': forms.NumberInput(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'min': '0',
            }),
            'delay_hours': forms.NumberInput(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'min': '0',
                'max': '23',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'メールの件名を入力',
            }),
            'body_html': forms.Textarea(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'rows': 15,
                'placeholder': 'HTML形式の本文を入力',
            }),
            'body_text': forms.Textarea(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'rows': 10,
                'placeholder': 'テキスト形式の本文を入力（任意）',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
        }


class CampaignForm(forms.ModelForm):
    target_tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
        }),
        required=False,
        label='ターゲットタグ',
    )

    class Meta:
        model = Campaign
        fields = ['name', 'subject', 'body_html', 'body_text', 'target_tags']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'キャンペーン名を入力',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'メールの件名を入力',
            }),
            'body_html': forms.Textarea(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'rows': 15,
                'placeholder': 'HTML形式の本文を入力',
            }),
            'body_text': forms.Textarea(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'rows': 10,
                'placeholder': 'テキスト形式の本文を入力（任意）',
            }),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['target_tags'].queryset = Tag.objects.filter(project=project)
