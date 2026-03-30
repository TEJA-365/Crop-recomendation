from django.contrib import admin
from django.utils.html import format_html
from .models import WeatherData


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    """Enhanced WeatherData admin."""
    list_display = ('date', 'get_location', 'temperature', 'rainfall', 'humidity', 'wind_speed', 'created_at')
    list_filter = ('date', 'created_at', 'updated_at')
    search_fields = ('latitude', 'longitude')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    list_per_page = 25
    
    fieldsets = (
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Date', {
            'fields': ('date',)
        }),
        ('Weather Conditions', {
            'fields': ('temperature', 'rainfall', 'humidity', 'wind_speed')
        }),
        ('Additional Data', {
            'fields': ('forecast_data',),
            'classes': ('collapse',),
            'description': 'Additional forecast data in JSON format'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_location(self, obj):
        """Display location coordinates."""
        return format_html(
            '<span class="text-muted">Lat: {:.6f}, Lng: {:.6f}</span>',
            obj.latitude,
            obj.longitude
        )
    get_location.short_description = 'Location'
