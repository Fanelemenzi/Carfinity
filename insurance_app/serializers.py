from rest_framework import serializers
from .models import *

class InsurancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePolicy
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    is_overdue = serializers.ReadOnlyField()
    days_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = MaintenanceSchedule
        fields = '__all__'
        read_only_fields = ('created_at',)

class MaintenanceComplianceSerializer(serializers.ModelSerializer):
    vehicle_info = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceCompliance
        fields = '__all__'
        read_only_fields = ('last_calculated',)
    
    def get_vehicle_info(self, obj):
        return {
            'vin': obj.vehicle.vin,
            'make': obj.vehicle.make,
            'model': obj.vehicle.model,
            'year': obj.vehicle.year
        }

class VehicleConditionScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleConditionScore
        fields = '__all__'
        read_only_fields = ('created_at', 'overall_score')
    
    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.calculate_overall_score()
        instance.save()
        return instance

class AccidentSerializer(serializers.ModelSerializer):
    vehicle_info = serializers.SerializerMethodField()
    detailed_accident_info = serializers.SerializerMethodField()
    has_vehicle_history = serializers.SerializerMethodField()
    
    class Meta:
        model = Accident
        fields = '__all__'
        read_only_fields = ('created_at',)
    
    def get_vehicle_info(self, obj):
        return {
            'vin': obj.vehicle.vin,
            'make': obj.vehicle.make,
            'model': obj.vehicle.model,
            'year': obj.vehicle.year
        }
    
    def get_detailed_accident_info(self, obj):
        return obj.get_detailed_accident_info()
    
    def get_has_vehicle_history(self, obj):
        return obj.vehicle_history is not None

class RiskAlertSerializer(serializers.ModelSerializer):
    vehicle_info = serializers.SerializerMethodField()
    
    class Meta:
        model = RiskAlert
        fields = '__all__'
        read_only_fields = ('created_at', 'resolved_date')
    
    def get_vehicle_info(self, obj):
        return {
            'vin': obj.vehicle.vin,
            'make': obj.vehicle.make,
            'model': obj.vehicle.model,
            'year': obj.vehicle.year,
            'policy_number': obj.vehicle.policy.policy_number
        }

class VehicleSerializer(serializers.ModelSerializer):
    maintenance_schedules = MaintenanceScheduleSerializer(many=True, read_only=True)
    compliance = MaintenanceComplianceSerializer(read_only=True)
    latest_condition_score = serializers.SerializerMethodField()
    active_alerts_count = serializers.SerializerMethodField()
    policy_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'vehicle_health_index', 'risk_score')
    
    def get_latest_condition_score(self, obj):
        latest = obj.condition_scores.first()
        if latest:
            return VehicleConditionScoreSerializer(latest).data
        return None
    
    def get_active_alerts_count(self, obj):
        return obj.risk_alerts.filter(is_resolved=False).count()
    
    def get_policy_info(self, obj):
        return {
            'policy_number': obj.policy.policy_number,
            'status': obj.policy.status
        }

class RiskAssessmentMetricsSerializer(serializers.ModelSerializer):
    policy_info = serializers.SerializerMethodField()
    
    class Meta:
        model = RiskAssessmentMetrics
        fields = '__all__'
        read_only_fields = ('calculation_date',)
    
    def get_policy_info(self, obj):
        return {
            'policy_number': obj.policy.policy_number,
            'policy_holder': obj.policy.policy_holder.username
        }