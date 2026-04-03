"""
Forms for crop recommendations.
"""
from django import forms
from apps.farms.models import Field


class RecommendationRequestForm(forms.Form):
    """Form for requesting crop recommendations."""
    
    field = forms.ModelChoiceField(
        queryset=Field.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
        }),
        help_text="Select a field to get crop recommendations"
    )
    
    include_weather = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        help_text="Include current weather data in recommendations"
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['field'].queryset = Field.objects.filter(farm__user=user)

