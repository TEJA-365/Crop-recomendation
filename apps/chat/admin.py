from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ChatConversation


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    """Enhanced ChatConversation admin."""
    list_display = ('get_user_link', 'get_language_badge', 'get_message_preview', 'get_response_preview', 'created_at')
    list_filter = ('language', 'created_at')
    search_fields = ('user__username', 'user__email', 'message', 'response')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'language')
        }),
        ('Conversation', {
            'fields': ('message', 'response')
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

    def get_language_badge(self, obj):
        """Display language with badge."""
        lang_display = dict(ChatConversation.LANGUAGE_CHOICES).get(obj.language, obj.language)
        return format_html(
            '<span class="badge bg-info">{}</span>',
            lang_display
        )
    get_language_badge.short_description = 'Language'
    get_language_badge.admin_order_field = 'language'

    def get_message_preview(self, obj):
        """Display message preview."""
        preview = obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
        return format_html('<span class="text-muted">{}</span>', preview)
    get_message_preview.short_description = 'Message'

    def get_response_preview(self, obj):
        """Display response preview."""
        preview = obj.response[:100] + '...' if len(obj.response) > 100 else obj.response
        return format_html('<span class="text-muted">{}</span>', preview)
    get_response_preview.short_description = 'Response'
