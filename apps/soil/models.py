from django.db import models
from apps.farms.models import Field


class SoilData(models.Model):
    """
    Soil data for a field from various sources.
    """
    SOURCE_CHOICES = [
        ('satellite', 'Satellite Data'),
        ('iot', 'IoT Sensor'),
        ('manual', 'Manual Input'),
        ('soil_grids', 'Soil Grids API'),
        ('bhuvan', 'Bhuvan API'),
    ]

    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='soil_data')
    ph = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Soil pH level (typically 0-14)"
    )
    moisture = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Soil moisture percentage"
    )
    n = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Nitrogen content in kg/hectare"
    )
    p = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Phosphorus content in kg/hectare"
    )
    k = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Potassium content in kg/hectare"
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='manual',
        help_text="Source of the soil data"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Soil Data"
        verbose_name_plural = "Soil Data"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Soil Data for {self.field.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
