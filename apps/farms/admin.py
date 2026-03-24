from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Farm, Field, CropHistory


class FieldInline(admin.TabularInline):
    """Inline admin for Fields within Farm."""
    model = Field
    extra = 0
    fields = ('name', 'area', 'soil_ph', 'soil_moisture', 'last_updated')
    readonly_fields = ('last_updated',)
    show_change_link = True


class CropHistoryInline(admin.TabularInline):
    """Inline admin for CropHistory within Field."""
    model = CropHistory
    extra = 0
    fields = ('crop_name', 'season', 'year', 'yield_achieved', 'profit')
    show_change_link = True


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    """Enhanced Farm admin."""
    list_display = ('name', 'get_user_link', 'get_field_count', 'area', 'soil_type', 'get_location', 'created_at')
    list_filter = ('soil_type', 'created_at', 'updated_at')
    search_fields = ('name', 'user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'get_field_count_display')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'
    inlines = [FieldInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Farm Details', {
            'fields': ('area', 'soil_type')
        }),
        ('Statistics', {
            'fields': ('get_field_count_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_user_link(self, obj):
        """Link to user admin."""
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    get_user_link.short_description = 'User'
    get_user_link.admin_order_field = 'user__username'

    def get_field_count(self, obj):
        """Display number of fields with link."""
        count = obj.fields.count()
        if count > 0:
            url = reverse('admin:farms_field_changelist') + f'?farm__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return '0'
    get_field_count.short_description = 'Fields'
    get_field_count.admin_order_field = 'fields__count'

    def get_field_count_display(self, obj):
        """Display field count in detail view."""
        return obj.fields.count()
    get_field_count_display.short_description = 'Total Fields'

    def get_location(self, obj):
        """Display location coordinates."""
        return format_html(
            '<span class="text-muted">Lat: {:.6f}, Lng: {:.6f}</span>',
            obj.latitude,
            obj.longitude
        )
    get_location.short_description = 'Location'


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    """Enhanced Field admin."""
    list_display = ('name', 'get_farm_link', 'area', 'get_soil_info', 'get_nutrient_info', 'get_crop_history_count', 'last_updated')
    list_filter = ('farm', 'last_updated', 'farm__soil_type')
    search_fields = ('name', 'farm__name', 'farm__user__username')
    readonly_fields = ('last_updated', 'get_crop_history_count_display')
    raw_id_fields = ('farm',)
    date_hierarchy = 'last_updated'
    inlines = [CropHistoryInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('farm', 'name')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Field Details', {
            'fields': ('area',)
        }),
        ('Soil Properties', {
            'fields': ('soil_ph', 'soil_moisture', 'n_content', 'p_content', 'k_content'),
            'description': 'Current soil properties (can be updated from SoilData)'
        }),
        ('Statistics', {
            'fields': ('get_crop_history_count_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )

    def get_farm_link(self, obj):
        """Link to farm admin."""
        url = reverse('admin:farms_farm_change', args=[obj.farm.pk])
        return format_html('<a href="{}">{}</a>', url, obj.farm.name)
    get_farm_link.short_description = 'Farm'
    get_farm_link.admin_order_field = 'farm__name'

    def get_soil_info(self, obj):
        """Display soil pH and moisture."""
        info = []
        if obj.soil_ph:
            info.append(f'pH: {obj.soil_ph}')
        if obj.soil_moisture:
            info.append(f'Moisture: {obj.soil_moisture}%')
        if info:
            return ', '.join(info)
        return '-'
    get_soil_info.short_description = 'Soil Info'

    def get_nutrient_info(self, obj):
        """Display nutrient content."""
        nutrients = []
        if obj.n_content:
            nutrients.append(f'N: {obj.n_content}')
        if obj.p_content:
            nutrients.append(f'P: {obj.p_content}')
        if obj.k_content:
            nutrients.append(f'K: {obj.k_content}')
        if nutrients:
            return format_html('<span class="text-muted">{}</span>', ', '.join(nutrients))
        return '-'
    get_nutrient_info.short_description = 'Nutrients (kg/ha)'

    def get_crop_history_count(self, obj):
        """Display crop history count with link."""
        count = obj.crop_history.count()
        if count > 0:
            url = reverse('admin:farms_crophistory_changelist') + f'?field__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return '0'
    get_crop_history_count.short_description = 'Crop History'
    get_crop_history_count.admin_order_field = 'crop_history__count'

    def get_crop_history_count_display(self, obj):
        """Display crop history count in detail view."""
        return obj.crop_history.count()
    get_crop_history_count_display.short_description = 'Total Crop History Records'


@admin.register(CropHistory)
class CropHistoryAdmin(admin.ModelAdmin):
    """Enhanced CropHistory admin."""
    list_display = ('crop_name', 'get_field_link', 'season', 'year', 'yield_achieved', 'profit', 'created_at')
    list_filter = ('season', 'year', 'crop_name', 'created_at')
    search_fields = ('crop_name', 'field__name', 'field__farm__name', 'field__farm__user__username', 'notes')
    readonly_fields = ('created_at',)
    raw_id_fields = ('field',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Field Information', {
            'fields': ('field',)
        }),
        ('Crop Information', {
            'fields': ('crop_name', 'season', 'year')
        }),
        ('Results', {
            'fields': ('yield_achieved', 'profit', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_field_link(self, obj):
        """Link to field admin."""
        url = reverse('admin:farms_field_change', args=[obj.field.pk])
        return format_html('<a href="{}">{}</a>', url, obj.field.name)
    get_field_link.short_description = 'Field'
    get_field_link.admin_order_field = 'field__name'
