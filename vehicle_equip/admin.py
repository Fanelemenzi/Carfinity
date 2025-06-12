# inspection/admin.py
from django.contrib import admin
from .models import Vehicle, PowertrainAndDrivetrain, ChassisSuspensionAndBraking

@admin.register(PowertrainAndDrivetrain)
class PowertrainAndDrivetrainAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle',
        'base_engine', 
        'transmission_type',
        'drive_layout',
        'fuel_system',
        'emissions_standard'
    )
    list_filter = (
        'transmission_type',
        'drive_layout',
        'fuel_system',
        'has_start_stop',
        'has_regenerative_braking'
    )
    search_fields = ('base_engine', 'transmission_specifications')
    list_select_related = ('vehicle',)
    fieldsets = (
        ('Vehicle', {
            'fields': ('vehicle',)
        }),
        ('Engine Specifications', {
            'fields': ('base_engine', 'engine_displacement', 'engine_power')
        }),
        ('Transmission Details', {
            'fields': (
                'transmission_specifications',
                'transmission_type',
                'gear_count'
            )
        }),
        ('Drivetrain Configuration', {
            'fields': ('drive_layout',)
        }),
        ('Fuel & Emissions', {
            'fields': ('fuel_system', 'emissions_standard')
        }),
        ('Advanced Features', {
            'fields': (
                'has_start_stop',
                'has_regenerative_braking'
            )
        }),
        ('Gearshift Interface', {
            'fields': (
                'gearshift_position',
                'gearshift_material'
            )
        }),
        ('Additional Information', {
            'fields': ('notes',)
        })
    )

# Admin view for Chassis Suspension and Braking
class ChassisSuspensionAndBrakingInline(admin.StackedInline):
    model = ChassisSuspensionAndBraking
    extra = 0
    fieldsets = (
        ('Suspension Systems', {
            'fields': ('front_suspension', 'rear_suspension')
        }),
        ('Brake Systems', {
            'fields': (
                'front_brake_type',
                'rear_brake_type',
                'brake_systems',
                'parking_brake_type'
            )
        }),
        ('Steering Systems', {
            'fields': (
                'steering_system',
                'steering_wheel_features'
            )
        }),
        ('Additional Features', {
            'fields': ('has_park_distance_control',)
        }),
    )

@admin.register(ChassisSuspensionAndBraking)
class ChassisSuspensionAndBrakingAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle',
        'front_suspension',
        'rear_suspension',
        'front_brake_type',
        'has_park_distance_control'
    )
    list_filter = (
        'front_suspension',
        'rear_suspension',
        'brake_systems'
    )
    search_fields = ('vehicle__make', 'vehicle__model')