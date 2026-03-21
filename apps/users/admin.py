from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Information'
    fk_name = 'user'
    fields = ('phone', 'latitude', 'longitude', 'preferred_language')
    extra = 0


class UserAdmin(BaseUserAdmin):
    """Enhanced User admin with profile inline."""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_full_name', 'is_staff', 'is_active', 'get_preferred_language', 'get_farm_count', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'profile__preferred_language')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__phone')
    list_select_related = ('profile',)
    ordering = ('-date_joined',)
    date_hierarchy = 'date_joined'
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    def get_preferred_language(self, instance):
        """Display preferred language."""
        if hasattr(instance, 'profile') and instance.profile:
            lang_display = dict(UserProfile.LANGUAGE_CHOICES).get(
                instance.profile.preferred_language, 
                instance.profile.preferred_language
            )
            return format_html(
                '<span class="badge bg-info">{}</span>',
                lang_display
            )
        return '-'
    get_preferred_language.short_description = 'Language'
    get_preferred_language.admin_order_field = 'profile__preferred_language'

    def get_farm_count(self, instance):
        """Display number of farms."""
        from apps.farms.models import Farm
        count = Farm.objects.filter(user=instance).count()
        if count > 0:
            return format_html(
                '<a href="/admin/farms/farm/?user__id__exact={}">{}</a>',
                instance.id,
                count
            )
        return '0'
    get_farm_count.short_description = 'Farms'
    get_farm_count.admin_order_field = 'farms__count'

    def get_inline_instances(self, request, obj=None):
        """Only show inline when editing existing user."""
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model."""
    list_display = ('user', 'phone', 'get_location', 'preferred_language', 'created_at', 'updated_at')
    list_filter = ('preferred_language', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('user', 'created_at', 'updated_at')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Contact Information', {
            'fields': ('phone',)
        }),
        ('Location', {
            'fields': ('latitude', 'longitude'),
            'description': 'Location coordinates for weather and soil data'
        }),
        ('Preferences', {
            'fields': ('preferred_language',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_location(self, obj):
        """Display location coordinates."""
        if obj.latitude and obj.longitude:
            return format_html(
                '<span class="text-muted">Lat: {:.6f}, Lng: {:.6f}</span>',
                obj.latitude,
                obj.longitude
            )
        return '-'
    get_location.short_description = 'Location'


# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
