from django import forms

from apps.contacts.models import Tag
from apps.emails.models import Scenario
from apps.members.models import Course
from apps.products.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'product_type', 'price',
            'billing_interval', 'grant_course', 'add_tag',
            'start_scenario', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '商品名を入力',
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': '商品の説明を入力',
            }),
            'product_type': forms.Select(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm bg-white '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'id': 'id_product_type',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '例: 9800',
                'min': '0',
            }),
            'billing_interval': forms.Select(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm bg-white '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'id': 'id_billing_interval',
            }),
            'grant_course': forms.Select(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm bg-white '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            }),
            'add_tag': forms.Select(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm bg-white '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            }),
            'start_scenario': forms.Select(attrs={
                'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg text-sm bg-white '
                         'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 '
                         'focus:ring-blue-500',
            }),
        }

    def __init__(self, *args, current_project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if current_project:
            self.fields['grant_course'].queryset = Course.objects.filter(
                site__project=current_project
            )
            self.fields['add_tag'].queryset = Tag.objects.filter(
                project=current_project
            )
            self.fields['start_scenario'].queryset = Scenario.objects.filter(
                project=current_project
            )
        else:
            self.fields['grant_course'].queryset = Course.objects.none()
            self.fields['add_tag'].queryset = Tag.objects.none()
            self.fields['start_scenario'].queryset = Scenario.objects.none()

        # Optional fields
        self.fields['grant_course'].required = False
        self.fields['add_tag'].required = False
        self.fields['start_scenario'].required = False
        self.fields['billing_interval'].required = False
        self.fields['description'].required = False

        # Empty labels
        self.fields['grant_course'].empty_label = '-- 選択しない --'
        self.fields['add_tag'].empty_label = '-- 選択しない --'
        self.fields['start_scenario'].empty_label = '-- 選択しない --'
