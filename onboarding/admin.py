from django.contrib import admin
from .models import PendingVehicleOnboarding
from django.utils import timezone
from vehicles.models import Vehicle, VehicleOwnership, VehicleStatus
from django_countries.fields import Country
from django.contrib.auth import get_user_model
from vehicle_equip.models import (
    PowertrainAndDrivetrain, ChassisSuspensionAndBraking, ElectricalSystem, ExteriorFeaturesAndBody, ActiveSafetyAndADAS
)
import datetime
from decimal import Decimal

User = get_user_model()

@admin.register(PendingVehicleOnboarding)
class PendingVehicleOnboardingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client', 'submitted_by', 'status', 'submitted_at', 'reviewed_at', 'reviewed_by'
    )
    list_filter = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('client__username', 'submitted_by__username', 'vehicle_data__vin')
    actions = ['approve_onboarding', 'reject_onboarding', 'create_full_vehicle_from_onboarding']

    def approve_onboarding(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='approved',
            reviewed_at=timezone.now(),
            reviewed_by=request.user
        )
        self.message_user(request, f"{updated} onboarding(s) approved.")
    approve_onboarding.short_description = "Approve selected onboardings"

    def reject_onboarding(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_at=timezone.now(),
            reviewed_by=request.user
        )
        self.message_user(request, f"{updated} onboarding(s) rejected.")
    reject_onboarding.short_description = "Reject selected onboardings"

    def parse_date(self, value):
        if not value:
            return None
        try:
            return datetime.datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None

    def parse_decimal(self, value):
        if value is None or value == '':
            return None
        try:
            return Decimal(value)
        except Exception:
            return None

    def create_full_vehicle_from_onboarding(self, request, queryset):
        created = 0
        for onboarding in queryset.filter(status='approved'):
            vdata = onboarding.vehicle_data
            sdata = onboarding.status_data
            edata = onboarding.equipment_data
            client = onboarding.client
            # 1. Vehicle
            try:
                vehicle, v_created = Vehicle.objects.get_or_create(
                    vin=vdata.get('vin'),
                    defaults={
                        'make': vdata.get('make'),
                        'model': vdata.get('model'),
                        'manufacture_year': int(vdata.get('manufacture_year')) if vdata.get('manufacture_year') else None,
                        'body_type': vdata.get('body_type'),
                        'engine_code': vdata.get('engine_code'),
                        'interior_color': vdata.get('interior_color'),
                        'exterior_color': vdata.get('exterior_color'),
                        'purchase_date': self.parse_date(vdata.get('purchase_date')),
                        'license_plate': vdata.get('license_plate'),
                        'fuel_type': vdata.get('fuel_type'),
                        'transmission_type': vdata.get('transmission_type'),
                        'powertrain_displacement': vdata.get('powertrain_displacement'),
                        'powertrain_power': vdata.get('powertrain_power'),
                        'plant_location': Country(vdata.get('plant_location')) if vdata.get('plant_location') else None,
                    }
                )
                # 2. VehicleOwnership
                VehicleOwnership.objects.get_or_create(
                    vehicle=vehicle,
                    user=client,
                    defaults={
                        'start_date': self.parse_date(vdata.get('start_date')) or timezone.now().date(),
                        'is_current_owner': True
                    }
                )
                # 3. VehicleStatus
                if sdata:
                    VehicleStatus.objects.update_or_create(
                        vehicle=vehicle,
                        defaults={
                            'accident_history': sdata.get('accident_history'),
                            'odometer_fraud': sdata.get('odometer_fraud'),
                            'theft_involvement': sdata.get('theft_involvement'),
                            'legal_status': sdata.get('legal_status'),
                            'owner_history': int(sdata.get('owner_history')) if sdata.get('owner_history') else 0
                        }
                    )
                # 4. Equipment Models
                if edata:
                    PowertrainAndDrivetrain.objects.update_or_create(
                        vehicle=vehicle,
                        defaults={
                            'base_engine': edata.get('base_engine'),
                            'engine_displacement': self.parse_decimal(edata.get('engine_displacement')),
                            'engine_power': edata.get('engine_power'),
                            'transmission_specifications': edata.get('transmission_specifications'),
                            'transmission_type': edata.get('transmission_type'),
                            'gear_count': edata.get('gear_count'),
                            'drive_layout': edata.get('drive_layout'),
                            'fuel_system': edata.get('fuel_system'),
                            'emissions_standard': edata.get('emissions_standard'),
                            'has_start_stop': edata.get('has_start_stop', False),
                            'has_regenerative_braking': edata.get('has_regenerative_braking', False),
                            'gearshift_position': edata.get('gearshift_position'),
                            'gearshift_material': edata.get('gearshift_material'),
                            'notes': edata.get('notes'),
                        }
                    )
                    ChassisSuspensionAndBraking.objects.update_or_create(
                        vehicle=vehicle,
                        defaults={
                            'front_suspension': edata.get('front_suspension'),
                            'rear_suspension': edata.get('rear_suspension'),
                            'front_brake_type': edata.get('front_brake_type'),
                            'rear_brake_type': edata.get('rear_brake_type'),
                            'brake_systems': edata.get('brake_systems'),
                            'parking_brake_type': edata.get('parking_brake_type'),
                            'steering_system': edata.get('steering_system'),
                            'steering_wheel_features': edata.get('steering_wheel_features'),
                            'has_park_distance_control': edata.get('has_park_distance_control', False),
                        }
                    )
                    ElectricalSystem.objects.update_or_create(
                        vehicle=vehicle,
                        defaults={
                            'primary_battery_type': edata.get('primary_battery_type'),
                            'primary_battery_capacity': edata.get('primary_battery_capacity'),
                            'has_second_battery': edata.get('has_second_battery', False),
                            'second_battery_type': edata.get('second_battery_type'),
                            'second_battery_capacity': edata.get('second_battery_capacity'),
                            'alternator_output': edata.get('alternator_output'),
                            'operating_voltage': edata.get('operating_voltage'),
                            'headlight_type': edata.get('headlight_type'),
                            'headlight_control': edata.get('headlight_control'),
                            'headlight_range_control': edata.get('headlight_range_control', False),
                            'instrument_cluster_type': edata.get('instrument_cluster_type'),
                            'socket_type': edata.get('socket_type'),
                            'horn_type': edata.get('horn_type'),
                        }
                    )
                    ExteriorFeaturesAndBody.objects.update_or_create(
                        vehicle=vehicle,
                        defaults={
                            'body_style': edata.get('body_style'),
                            'windshield_type': edata.get('windshield_type'),
                            'side_windows_type': edata.get('side_windows_type'),
                            'has_chrome_package': edata.get('has_chrome_package', False),
                            'has_roof_rails': edata.get('has_roof_rails', False),
                            'roof_type': edata.get('roof_type'),
                            'has_front_fog_lamp': edata.get('has_front_fog_lamp', False),
                            'has_rear_fog_lamp': edata.get('has_rear_fog_lamp', False),
                            'has_headlight_range_control': edata.get('has_headlight_range_control', False),
                            'has_scuff_plates': edata.get('has_scuff_plates', False),
                            'has_loading_edge_protection': edata.get('has_loading_edge_protection', False),
                            'has_front_underbody_guard': edata.get('has_front_underbody_guard', False),
                            'wheel_type': edata.get('wheel_type'),
                            'has_wheel_covers': edata.get('has_wheel_covers', False),
                            'has_lockable_wheel_bolts': edata.get('has_lockable_wheel_bolts', False),
                            'has_spare_wheel': edata.get('has_spare_wheel', False),
                            'has_trailer_hitch': edata.get('has_trailer_hitch', False),
                            'tailgate_lock_type': edata.get('tailgate_lock_type'),
                            'left_mirror_type': edata.get('left_mirror_type'),
                            'right_mirror_type': edata.get('right_mirror_type'),
                            'antenna_type': edata.get('antenna_type'),
                        }
                    )
                    ActiveSafetyAndADAS.objects.update_or_create(
                        vehicle=vehicle,
                        defaults={
                            'cruise_control_system': edata.get('cruise_control_system'),
                            'has_speed_limiter': edata.get('has_speed_limiter', False),
                            'park_distance_control': edata.get('park_distance_control'),
                            'driver_alert_system': edata.get('driver_alert_system'),
                            'tire_pressure_monitoring': edata.get('tire_pressure_monitoring'),
                            'lane_assist_system': edata.get('lane_assist_system'),
                            'blind_spot_monitoring': edata.get('blind_spot_monitoring'),
                            'collision_warning_system': edata.get('collision_warning_system'),
                            'has_cross_traffic_alert': edata.get('has_cross_traffic_alert', False),
                            'has_traffic_sign_recognition': edata.get('has_traffic_sign_recognition', False),
                        }
                    )
                created += 1
            except Exception as e:
                self.message_user(request, f"Error creating full vehicle for onboarding {onboarding.id}: {e}", level='error')
        self.message_user(request, f"{created} full vehicle(s) and related records created from approved onboarding records.")
    create_full_vehicle_from_onboarding.short_description = "Create full Vehicle & related records from approved onboarding(s)"
