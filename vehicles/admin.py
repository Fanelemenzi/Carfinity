from django.contrib import admin
from .models import Vehicle, VehicleOwnership, VehicleHistory, VehicleStatus, VehicleImage
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

# Register your models here.

class VehicleImageInline(admin.TabularInline):
    model = VehicleImage
    extra = 1
    fields = ('image', 'image_type', 'description', 'is_primary', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    get_image_preview.short_description = 'Preview'

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vin', 'make', 'model', 'manufacture_year', 'get_image_count', 'get_primary_image')
    search_fields = ('vin', 'make', 'model')
    list_filter = ('fuel_type', 'transmission_type', 'manufacture_year')
    inlines = [VehicleImageInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Vehicle Information', {
            'fields': ('vin', 'make', 'model', 'manufacture_year', 'body_type')
        }),
        ('Technical Details', {
            'fields': ('engine_code', 'fuel_type', 'transmission_type', 'powertrain_displacement', 'powertrain_power')
        }),
        ('Appearance', {
            'fields': ('interior_color', 'exterior_color')
        }),
        ('Additional Information', {
            'fields': ('purchase_date', 'license_plate', 'plant_location')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_image_count(self, obj):
        count = obj.images.count()
        if count > 0:
            return format_html(
                '<a href="{}?vehicle__id__exact={}">{}</a>',
                reverse('admin:vehicles_vehicleimage_changelist'),
                obj.id,
                f"{count} image{'s' if count != 1 else ''}"
            )
        return "0 images"
    get_image_count.short_description = 'Images'
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            return format_html(
                '<img src="{}" style="max-height: 40px; max-width: 40px; object-fit: cover; border-radius: 4px;" />',
                primary_image.image.url
            )
        return "No primary image"
    get_primary_image.short_description = 'Primary Image'

@admin.register(VehicleImage)
class VehicleImageAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'image_type', 'get_image_preview', 'is_primary', 'uploaded_by', 'uploaded_at')
    list_filter = ('image_type', 'is_primary', 'uploaded_at', 'vehicle__make', 'vehicle__model')
    search_fields = ('vehicle__vin', 'vehicle__make', 'vehicle__model', 'description')
    readonly_fields = ('uploaded_at', 'get_image_preview_large')
    list_editable = ('is_primary',)
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Image Information', {
            'fields': ('vehicle', 'image', 'image_type', 'description', 'is_primary')
        }),
        ('Upload Details', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
        ('Preview', {
            'fields': ('get_image_preview_large',),
            'classes': ('collapse',)
        }),
    )
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No image"
    get_image_preview.short_description = 'Preview'
    
    def get_image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100%; max-height: 400px; object-fit: contain;" />',
                obj.image.url
            )
        return "No image"
    get_image_preview_large.short_description = 'Image Preview'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set uploaded_by on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(VehicleOwnership)
class VehicleOwnershipAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'user', 'start_date', 'end_date', 'is_current_owner')
    search_fields = ('vehicle__vin', 'user__email')
    list_filter = ('is_current_owner',)

@admin.register(VehicleHistory)
class VehicleHistoryAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'event_type', 'event_date', 'reported_by', 'verified')
    search_fields = ('vehicle__vin', 'event_type', 'description')
    list_filter = ('event_type', 'verified', 'event_date')

@admin.register(VehicleStatus)
class VehicleStatus(admin.ModelAdmin):
    list_display= ('vehicle', 'accident_history', 'odometer_fraud', 'theft_involvement', 'legal_status', 'owner_history')
    #search_fields = ('vehicle__vin')
    #list_filter = ('vehicle__vin')