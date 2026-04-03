from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """Enhanced Recommendation admin."""
    list_display = ('crop_name', 'get_user_link', 'get_field_link', 'get_confidence_badge', 'expected_yield', 'profit_margin', 'get_sustainability_badge', 'created_at')
    list_filter = ('crop_name', 'created_at', 'confidence_score', 'sustainability_score')
    search_fields = ('crop_name', 'user__username', 'field__name', 'field__farm__name')
    readonly_fields = ('created_at', 'get_reasoning_display')
    raw_id_fields = ('user', 'field')
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('User and Field', {
            'fields': ('user', 'field')
        }),
        ('Recommendation', {
            'fields': ('crop_name', 'confidence_score')
        }),
        ('Predictions', {
            'fields': ('expected_yield', 'profit_margin', 'sustainability_score')
        }),
        ('Reasoning', {
            'fields': ('reasoning', 'get_reasoning_display'),
            'classes': ('collapse',),
            'description': 'Detailed reasoning for the recommendation'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_user_link(self, obj):
        """Link to user admin."""
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    get_user_link.short_description = 'User'
    get_user_link.admin_order_field = 'user__username'

    def get_field_link(self, obj):
        """Link to field admin."""
        url = reverse('admin:farms_field_change', args=[obj.field.pk])
        return format_html('<a href="{}">{}</a>', url, obj.field.name)
    get_field_link.short_description = 'Field'
    get_field_link.admin_order_field = 'field__name'

    def get_confidence_badge(self, obj):
        """Display confidence score with color-coded badge."""
        if obj.confidence_score >= 80:
            color = 'success'
        elif obj.confidence_score >= 60:
            color = 'warning'
        else:
            color = 'secondary'
        return format_html(
            '<span class="badge bg-{}">{:.1f}%</span>',
            color,
            obj.confidence_score
        )
    get_confidence_badge.short_description = 'Confidence'
    get_confidence_badge.admin_order_field = 'confidence_score'

    def get_sustainability_badge(self, obj):
        """Display sustainability score with color-coded badge."""
        if obj.sustainability_score >= 80:
            color = 'success'
        elif obj.sustainability_score >= 60:
            color = 'info'
        else:
            color = 'warning'
        return format_html(
            '<span class="badge bg-{}">{:.1f}</span>',
            color,
            obj.sustainability_score
        )
    get_sustainability_badge.short_description = 'Sustainability'
    get_sustainability_badge.admin_order_field = 'sustainability_score'

    def get_reasoning_display(self, obj):
        """Display reasoning in a readable format."""
        if obj.reasoning:
            import json
            try:
                reasoning = json.dumps(obj.reasoning, indent=2)
                return format_html('<pre>{}</pre>', reasoning)
            except:
                return str(obj.reasoning)
        return '-'
    get_reasoning_display.short_description = 'Reasoning (Formatted)'
