"""
Forms for soil data input and management.
"""
from django import forms
from .models import SoilData
from apps.farms.models import Field


class SoilDataForm(forms.ModelForm):
    """Form for manual soil data input."""
    
    class Meta:
        model = SoilData
        fields = ('field', 'ph', 'moisture', 'n', 'p', 'k', 'source')
        widgets = {
            'field': forms.Select(attrs={
                'class': 'form-control',
            }),
            'ph': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'pH (0-14)',
                'step': '0.1',
                'min': '0',
                'max': '14'
            }),
            'moisture': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Moisture (%)',
                'step': '0.1',
                'min': '0',
                'max': '100'
            }),
            'n': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nitrogen (kg/ha)',
                'step': '0.1',
                'min': '0'
            }),
            'p': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phosphorus (kg/ha)',
                'step': '0.1',
                'min': '0'
            }),
            'k': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Potassium (kg/ha)',
                'step': '0.1',
                'min': '0'
            }),
            'source': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Filter fields to only show user's fields
            self.fields['field'].queryset = Field.objects.filter(farm__user=user)
        self.fields['source'].initial = 'manual'
        # Make fields required for manual input (even though they're nullable in model)
        self.fields['ph'].required = True
        self.fields['moisture'].required = True
        self.fields['n'].required = True
        self.fields['p'].required = True
        self.fields['k'].required = True


class SoilDataFetchForm(forms.Form):
    """Form for fetching soil data from APIs."""
    
    SOURCE_CHOICES = [
        ('auto', 'Auto (Best Available)'),
        ('soil_grids', 'Soil Grids API'),
        ('bhuvan', 'Bhuvan API (India)'),
    ]
    
    field = forms.ModelChoiceField(
        queryset=Field.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="Select a field to fetch soil data for"
    )
    source = forms.ChoiceField(
        choices=SOURCE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        initial='auto',
        help_text="Choose data source"
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['field'].queryset = Field.objects.filter(farm__user=user)

