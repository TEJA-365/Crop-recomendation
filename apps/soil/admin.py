from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import SoilData


@admin.register(SoilData)
class SoilDataAdmin(admin.ModelAdmin):
    """Enhanced SoilData admin."""
    list_display = ('get_field_link', 'ph', 'moisture', 'get_nutrients', 'source', 'get_source_badge', 'timestamp')
    list_filter = ('source', 'timestamp', 'field__farm')
    search_fields = ('field__name', 'field__farm__name', 'field__farm__user__username')
    readonly_fields = ('timestamp',)
    raw_id_fields = ('field',)
    date_hierarchy = 'timestamp'
    list_per_page = 25
    
    fieldsets = (
        ('Field Information', {
            'fields': ('field',)
        }),
        ('Soil Properties', {
            'fields': ('ph', 'moisture')
        }),
        ('Nutrient Content (kg/hectare)', {
            'fields': ('n', 'p', 'k')
        }),
        ('Data Source', {
            'fields': ('source', 'timestamp')
        }),
    )

    def get_field_link(self, obj):
        """Link to field admin."""
        url = reverse('admin:farms_field_change', args=[obj.field.pk])
        return format_html('<a href="{}">{}</a>', url, obj.field.name)
    get_field_link.short_description = 'Field'
    get_field_link.admin_order_field = 'field__name'

    def get_nutrients(self, obj):
        """Display nutrient content."""
        return format_html(
            '<span class="text-muted">N: {} | P: {} | K: {}</span>',
            obj.n,
            obj.p,
            obj.k
        )
    get_nutrients.short_description = 'Nutrients (N-P-K)'

    def get_source_badge(self, obj):
        """Display source with badge."""
        source_colors = {
            'satellite': 'primary',
            'iot': 'success',
            'manual': 'secondary',
            'soil_grids': 'info',
            'bhuvan': 'warning',
        }
        color = source_colors.get(obj.source, 'secondary')
        source_display = dict(SoilData.SOURCE_CHOICES).get(obj.source, obj.source)
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            source_display
        )
    get_source_badge.short_description = 'Source'
