from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class WeatherData(models.Model):
    """
    Weather data for a specific location and date.
    """
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Location latitude"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Location longitude"
    )
    date = models.DateField(help_text="Date of the weather data")
    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Temperature in Celsius"
    )
    rainfall = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Rainfall in mm"
    )
    humidity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Humidity percentage"
    )
    wind_speed = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Wind speed in km/h"
    )
    forecast_data = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Additional forecast data in JSON format"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Weather Data"
        verbose_name_plural = "Weather Data"
        ordering = ['-date', '-created_at']
        unique_together = ['latitude', 'longitude', 'date']

    def __str__(self):
        return f"Weather Data - {self.date} ({self.latitude}, {self.longitude})"
