# inspection/admin.py
from django.contrib import admin
from .models import Vehicle, PowertrainAndDrivetrain, ChassisSuspensionAndBraking, ElectricalSystem, ExteriorFeaturesAndBody

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

class ElectricalSystemInline(admin.StackedInline):
    model = ElectricalSystem
    extra = 0
    fieldsets = (
        ('Battery System', {
            'fields': (
                'primary_battery_type',
                'primary_battery_capacity',
                'has_second_battery',
                'second_battery_type',
                'second_battery_capacity'
            )
        }),
        ('Charging System', {
            'fields': (
                'alternator_output',
                'operating_voltage'
            )
        }),
        ('Lighting Systems', {
            'fields': (
                'headlight_type',
                'headlight_control',
                'headlight_range_control'
            )
        }),
        ('Instrumentation', {
            'fields': ('instrument_cluster_type',)
        }),
        ('Additional Components', {
            'fields': (
                'socket_type',
                'horn_type'
            )
        }),
    )

@admin.register(ElectricalSystem)
class ElectricalSystemAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle',
        'get_voltage_display',
        'headlight_type',
        'instrument_cluster_type'
    )
    list_filter = (
        'operating_voltage',
        'headlight_type',
        'has_second_battery'
    )
    search_fields = ('vehicle__make', 'vehicle__model')
    
    def get_voltage_display(self, obj):
        return obj.get_operating_voltage_display()
    get_voltage_display.short_description = 'Voltage System'

class ExteriorFeaturesAndBodyInline(admin.StackedInline):
    model = ExteriorFeaturesAndBody
    extra = 0
    fieldsets = (
        ('Body Structure', {
            'fields': (
                'body_style',
                'windshield_type',
                'side_windows_type'
            )
        }),
        ('Exterior Features', {
            'fields': (
                'has_chrome_package',
                'has_roof_rails',
                'roof_type',
                'has_scuff_plates'
            )
        }),
        ('Lighting', {
            'fields': (
                'has_front_fog_lamp',
                'has_rear_fog_lamp',
                'has_headlight_range_control'
            )
        }),
        ('Protection Features', {
            'fields': (
                'has_loading_edge_protection',
                'has_front_underbody_guard'
            )
        }),
        ('Wheels & Tires', {
            'fields': (
                'wheel_type',
                'has_wheel_covers',
                'has_lockable_wheel_bolts',
                'has_spare_wheel'
            )
        }),
        ('Functional Features', {
            'fields': (
                'has_trailer_hitch',
                'tailgate_lock_type'
            )
        }),
        ('Mirrors & Antennas', {
            'fields': (
                'left_mirror_type',
                'right_mirror_type',
                'antenna_type'
            )
        }),
    )

@admin.register(ExteriorFeaturesAndBody)
class ExteriorFeaturesAndBodyAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle',
        'get_body_style_display',
        'has_roof_rails',
        'has_trailer_hitch'
    )
    list_filter = (
        'body_style',
        'roof_type',
        'has_front_fog_lamp'
    )
    search_fields = ('vehicle__make', 'vehicle__model')
