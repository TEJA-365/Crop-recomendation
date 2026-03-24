"""
Forms for farm and field management.
"""
from django import forms
from django.db.models import Sum
from decimal import Decimal
from .models import Farm, Field


class FarmForm(forms.ModelForm):
    """Form for creating and editing farms."""
    
    class Meta:
        model = Farm
        fields = ('name', 'latitude', 'longitude', 'area', 'soil_type')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Farm name'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Latitude',
                'step': 'any'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Longitude',
                'step': 'any'
            }),
            'area': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Area in hectares',
                'step': '0.01',
                'min': '0.01'
            }),
            'soil_type': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['soil_type'].required = False


class FieldForm(forms.ModelForm):
    """Form for creating and editing fields."""
    
    class Meta:
        model = Field
        fields = ('farm', 'name', 'latitude', 'longitude', 'area')
        widgets = {
            'farm': forms.Select(attrs={
                'class': 'form-control'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Field name'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Latitude (optional)',
                'step': 'any'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Longitude (optional)',
                'step': 'any'
            }),
            'area': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Area in hectares',
                'step': '0.01',
                'min': '0.01'
            }),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Filter farms to only show user's farms
            self.fields['farm'].queryset = Farm.objects.filter(user=user)
            # Make farm required if creating new field
            if not self.instance.pk:
                self.fields['farm'].required = True
    
    def clean(self):
        """Validate that total field area doesn't exceed farm area."""
        cleaned_data = super().clean()
        farm = cleaned_data.get('farm')
        area = cleaned_data.get('area')
        
        if farm and area:
            # Calculate total area of existing fields (excluding current field if updating)
            existing_fields = farm.fields.exclude(pk=self.instance.pk if self.instance.pk else None)
            total_existing_area = existing_fields.aggregate(
                total=Sum('area')
            )['total'] or Decimal('0.00')
            
            # Calculate total area including the new/updated field
            total_area = total_existing_area + Decimal(str(area))
            
            # Check if total exceeds farm area
            if total_area > farm.area:
                available_area = farm.area - total_existing_area
                raise forms.ValidationError(
                    f"Total field area ({total_area:.2f} ha) exceeds farm area ({farm.area:.2f} ha). "
                    f"Available area for new fields: {available_area:.2f} ha. "
                    f"Please reduce the field area to {available_area:.2f} ha or less."
                )
        
        return cleaned_data

