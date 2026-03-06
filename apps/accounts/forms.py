from django import forms
from django.contrib.auth.forms import UserCreationForm

from apps.accounts.models import User, Project


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label='メールアドレス')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'slug')
        labels = {
            'name': 'プロジェクト名',
            'slug': 'スラッグ（URL用）',
        }
        help_texts = {
            'slug': '半角英数字とハイフンのみ使用できます。',
        }
