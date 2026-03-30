"""
Forms for weather data management.
"""
from django import forms
from .models import WeatherData
from apps.farms.models import Farm, Field


class WeatherDataFetchForm(forms.Form):
    """Form for fetching weather data from API."""
    
    LOCATION_CHOICES = [
        ('field', 'Field Location'),
        ('farm', 'Farm Location'),
        ('custom', 'Custom Coordinates'),
    ]
    
    location_type = forms.ChoiceField(
        choices=LOCATION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        initial='field',
        help_text="Choose location source"
    )
    
    field = forms.ModelChoiceField(
        queryset=Field.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="Select a field"
    )
    
    farm = forms.ModelChoiceField(
        queryset=Farm.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="Select a farm"
    )
    
    latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Latitude',
            'step': 'any'
        }),
        help_text="Custom latitude"
    )
    
    longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Longitude',
            'step': 'any'
        }),
        help_text="Custom longitude"
    )
    
    forecast_days = forms.IntegerField(
        min_value=1,
        max_value=7,
        initial=7,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '7'
        }),
        help_text="Number of forecast days (1-7)"
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['field'].queryset = Field.objects.filter(farm__user=user)
            self.fields['farm'].queryset = Farm.objects.filter(user=user)
    
    def clean(self):
        cleaned_data = super().clean()
        location_type = cleaned_data.get('location_type')
        
        if location_type == 'field':
            if not cleaned_data.get('field'):
                raise forms.ValidationError("Please select a field.")
            field = cleaned_data['field']
            if not field.latitude or not field.longitude:
                if not field.farm.latitude or not field.farm.longitude:
                    raise forms.ValidationError("Field or farm location is required.")
        
        elif location_type == 'farm':
            if not cleaned_data.get('farm'):
                raise forms.ValidationError("Please select a farm.")
            farm = cleaned_data['farm']
            if not farm.latitude or not farm.longitude:
                raise forms.ValidationError("Farm location is required.")
        
        elif location_type == 'custom':
            if not cleaned_data.get('latitude') or not cleaned_data.get('longitude'):
                raise forms.ValidationError("Custom coordinates are required.")
        
        return cleaned_data


class WeatherDataManualForm(forms.ModelForm):
    """Form for manual weather data input."""
    
    class Meta:
        model = WeatherData
        fields = ('latitude', 'longitude', 'date', 'temperature', 'rainfall', 'humidity', 'wind_speed', 'forecast_data')
        widgets = {
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Temperature (°C)',
                'step': '0.1'
            }),
            'rainfall': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rainfall (mm)',
                'step': '0.1',
                'min': '0'
            }),
            'humidity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Humidity (%)',
                'step': '0.1',
                'min': '0',
                'max': '100'
            }),
            'wind_speed': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Wind Speed (km/h)',
                'step': '0.1',
                'min': '0'
            }),
        }

