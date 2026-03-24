from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Farm(models.Model):
    """
    Represents a farm owned by a user.
    """
    SOIL_TYPE_CHOICES = [
        ('clay', 'Clay'),
        ('sandy', 'Sandy'),
        ('loamy', 'Loamy'),
        ('silt', 'Silt'),
        ('peat', 'Peat'),
        ('chalky', 'Chalky'),
        ('unknown', 'Unknown'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
    name = models.CharField(max_length=200, help_text="Name of the farm")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Farm location latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Farm location longitude")
    area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Farm area in hectares"
    )
    soil_type = models.CharField(
        max_length=20,
        choices=SOIL_TYPE_CHOICES,
        default='unknown',
        help_text="Type of soil in the farm"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Farm"
        verbose_name_plural = "Farms"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Field(models.Model):
    """
    Represents a field within a farm.
    """
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=200, help_text="Name of the field")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Field center latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Field center longitude")
    area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Field area in hectares"
    )
    # Soil properties (can be updated from SoilData)
    soil_ph = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True, help_text="Soil pH level")
    soil_moisture = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Soil moisture percentage")
    n_content = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Nitrogen content (kg/ha)")
    p_content = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Phosphorus content (kg/ha)")
    k_content = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Potassium content (kg/ha)")
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Field"
        verbose_name_plural = "Fields"
        ordering = ['farm', 'name']

    def __str__(self):
        return f"{self.name} ({self.farm.name})"


class CropHistory(models.Model):
    """
    Historical crop data for a field.
    """
    SEASON_CHOICES = [
        ('kharif', 'Kharif (Monsoon)'),
        ('rabi', 'Rabi (Winter)'),
        ('zaid', 'Zaid (Summer)'),
        ('year_round', 'Year Round'),
    ]

    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='crop_history')
    crop_name = models.CharField(max_length=100, help_text="Name of the crop grown")
    season = models.CharField(max_length=20, choices=SEASON_CHOICES, help_text="Season when crop was grown")
    year = models.IntegerField(help_text="Year when crop was grown")
    yield_achieved = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Yield achieved in kg/hectare"
    )
    profit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Profit made in local currency"
    )
    notes = models.TextField(blank=True, null=True, help_text="Additional notes about the crop")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Crop History"
        verbose_name_plural = "Crop Histories"
        ordering = ['-year', '-season']
        unique_together = ['field', 'crop_name', 'season', 'year']

    def __str__(self):
        return f"{self.crop_name} - {self.season} {self.year} ({self.field.name})"
