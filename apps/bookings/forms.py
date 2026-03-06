from django import forms

from apps.bookings.models import (
    BookingType, BookingAvailability, BookingBlockedDate,
    CalendarIntegration, ZoomIntegration,
)
from apps.contacts.models import Tag
from apps.emails.models import Scenario

TW = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
TW_SELECT = TW + ' bg-white'
TW_CHECK = 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'


class BookingTypeForm(forms.ModelForm):
    class Meta:
        model = BookingType
        exclude = ['project', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': TW}),
            'slug': forms.TextInput(attrs={'class': TW}),
            'description': forms.Textarea(attrs={'class': TW, 'rows': 3}),
            'duration_minutes': forms.NumberInput(attrs={'class': TW}),
            'location_type': forms.Select(attrs={'class': TW_SELECT}),
            'location_detail': forms.TextInput(attrs={'class': TW}),
            'buffer_before_minutes': forms.NumberInput(attrs={'class': TW}),
            'buffer_after_minutes': forms.NumberInput(attrs={'class': TW}),
            'max_bookings_per_day': forms.NumberInput(attrs={'class': TW}),
            'add_tag': forms.Select(attrs={'class': TW_SELECT}),
            'start_scenario': forms.Select(attrs={'class': TW_SELECT}),
            'confirmation_subject': forms.TextInput(attrs={'class': TW}),
            'confirmation_body': forms.Textarea(attrs={'class': TW, 'rows': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CHECK}),
        }

    def __init__(self, *args, current_project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if current_project:
            self.fields['add_tag'].queryset = Tag.objects.filter(project=current_project)
            self.fields['start_scenario'].queryset = Scenario.objects.filter(
                project=current_project
            )
        self.fields['add_tag'].required = False
        self.fields['add_tag'].empty_label = '-- 選択しない --'
        self.fields['start_scenario'].required = False
        self.fields['start_scenario'].empty_label = '-- 選択しない --'


class BookingAvailabilityForm(forms.ModelForm):
    class Meta:
        model = BookingAvailability
        fields = ['day_of_week', 'start_time', 'end_time', 'is_active']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': TW_SELECT}),
            'start_time': forms.TimeInput(attrs={'class': TW, 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': TW, 'type': 'time'}),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CHECK}),
        }


class BookingBlockedDateForm(forms.ModelForm):
    class Meta:
        model = BookingBlockedDate
        fields = ['date', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'class': TW, 'type': 'date'}),
            'reason': forms.TextInput(attrs={'class': TW}),
        }


class CalendarIntegrationForm(forms.ModelForm):
    class Meta:
        model = CalendarIntegration
        fields = ['credentials_json', 'calendar_id', 'is_active']
        widgets = {
            'credentials_json': forms.Textarea(attrs={'class': TW, 'rows': 6}),
            'calendar_id': forms.TextInput(attrs={'class': TW}),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CHECK}),
        }


class ZoomIntegrationForm(forms.ModelForm):
    class Meta:
        model = ZoomIntegration
        fields = ['account_id', 'client_id', 'client_secret', 'is_active']
        widgets = {
            'account_id': forms.TextInput(attrs={'class': TW}),
            'client_id': forms.TextInput(attrs={'class': TW}),
            'client_secret': forms.PasswordInput(attrs={'class': TW}, render_value=True),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CHECK}),
        }


class PublicBookingForm(forms.Form):
    email = forms.EmailField(
        label='メールアドレス',
        widget=forms.EmailInput(attrs={'class': TW}),
    )
    name = forms.CharField(
        label='お名前',
        widget=forms.TextInput(attrs={'class': TW}),
    )
    phone = forms.CharField(
        label='電話番号',
        required=False,
        widget=forms.TextInput(attrs={'class': TW}),
    )
    memo = forms.CharField(
        label='メモ',
        required=False,
        widget=forms.Textarea(attrs={'class': TW, 'rows': 3}),
    )
