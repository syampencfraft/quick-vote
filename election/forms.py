from django import forms
from django.utils import timezone
from .models import Election, Candidate


class FlexibleDateTimeInput(forms.DateTimeInput):
    """
    A DateTimeInput rendered as datetime-local with the correct value format
    and a min attribute set to the current time, preventing past date selection.
    """
    def __init__(self, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].update({'type': 'datetime-local', 'class': 'form-control'})
        super().__init__(format='%Y-%m-%dT%H:%M', **kwargs)

    def get_context(self, name, value, attrs):
        # Dynamically set min to current time so browser blocks past dates
        now_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M')
        attrs = attrs or {}
        attrs['min'] = now_str
        return super().get_context(name, value, attrs)


class ElectionForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        widget=FlexibleDateTimeInput(),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
    )
    end_date = forms.DateTimeField(
        widget=FlexibleDateTimeInput(),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
    )

    class Meta:
        model = Election
        fields = ['title', 'description', 'start_date', 'end_date', 'is_active', 'results_published']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_start_date(self):
        start = self.cleaned_data.get('start_date')
        if start and start < timezone.now():
            raise forms.ValidationError("Start date cannot be in the past.")
        return start

    def clean_end_date(self):
        end = self.cleaned_data.get('end_date')
        if end and end < timezone.now():
            raise forms.ValidationError("End date cannot be in the past.")
        return end

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end <= start:
            raise forms.ValidationError("End date must be after the start date.")
        return cleaned_data


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['name', 'details', 'symbol']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'details': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'symbol': forms.FileInput(attrs={'class': 'form-control'}),
        }
