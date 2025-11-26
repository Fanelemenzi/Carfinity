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
            'year': obj.vehicle.manufacture_year
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
            'year': obj.vehicle.manufacture_year
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
            'year': obj.vehicle.manufacture_year,
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


# Parts-Based Quote System Serializers

class DamagedPartSerializer(serializers.ModelSerializer):
    estimated_cost_range = serializers.SerializerMethodField()
    quote_count = serializers.SerializerMethodField()
    has_market_average = serializers.SerializerMethodField()
    assessment_info = serializers.SerializerMethodField()
    
    class Meta:
        model = DamagedPart
        fields = '__all__'
        read_only_fields = ('identified_date',)
    
    def get_estimated_cost_range(self, obj):
        return obj.get_estimated_cost_range()
    
    def get_quote_count(self, obj):
        return obj.quotes.count()
    
    def get_has_market_average(self, obj):
        return hasattr(obj, 'market_average')
    
    def get_assessment_info(self, obj):
        return {
            'assessment_id': obj.assessment.assessment_id,
            'vehicle_make': obj.assessment.vehicle.make,
            'vehicle_model': obj.assessment.vehicle.model,
            'vehicle_year': obj.assessment.vehicle.manufacture_year
        }


class PartQuoteRequestSerializer(serializers.ModelSerializer):
    selected_providers = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    quote_count = serializers.SerializerMethodField()
    damaged_part_info = serializers.SerializerMethodField()
    
    class Meta:
        model = PartQuoteRequest
        fields = '__all__'
        read_only_fields = ('request_id', 'request_date', 'dispatched_at', 'vehicle_make', 'vehicle_model', 'vehicle_year', 'vehicle_vin')
    
    def get_selected_providers(self, obj):
        return obj.get_selected_providers()
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_quote_count(self, obj):
        return obj.quotes.count()
    
    def get_damaged_part_info(self, obj):
        return {
            'part_name': obj.damaged_part.part_name,
            'part_category': obj.damaged_part.part_category,
            'damage_severity': obj.damaged_part.damage_severity
        }


class PartQuoteSerializer(serializers.ModelSerializer):
    cost_breakdown = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    price_score = serializers.SerializerMethodField()
    quote_request_info = serializers.SerializerMethodField()
    
    class Meta:
        model = PartQuote
        fields = '__all__'
        read_only_fields = ('quote_date', 'total_cost')
    
    def get_cost_breakdown(self, obj):
        return obj.get_cost_breakdown()
    
    def get_is_valid(self, obj):
        return obj.is_valid()
    
    def get_price_score(self, obj):
        if hasattr(obj.damaged_part, 'market_average'):
            market_avg = float(obj.damaged_part.market_average.average_total_cost)
            return obj.calculate_price_score(market_avg)
        return None
    
    def get_quote_request_info(self, obj):
        return {
            'request_id': obj.quote_request.request_id,
            'part_name': obj.damaged_part.part_name
        }


class PartMarketAverageSerializer(serializers.ModelSerializer):
    price_range_display = serializers.SerializerMethodField()
    is_high_confidence = serializers.SerializerMethodField()
    variance_category = serializers.SerializerMethodField()
    damaged_part_info = serializers.SerializerMethodField()
    
    class Meta:
        model = PartMarketAverage
        fields = '__all__'
        read_only_fields = ('calculated_date', 'last_updated')
    
    def get_price_range_display(self, obj):
        return obj.get_price_range_display()
    
    def get_is_high_confidence(self, obj):
        return obj.is_high_confidence()
    
    def get_variance_category(self, obj):
        return obj.get_variance_category()
    
    def get_damaged_part_info(self, obj):
        return {
            'part_name': obj.damaged_part.part_name,
            'part_category': obj.damaged_part.part_category,
            'assessment_id': obj.damaged_part.assessment.assessment_id
        }


class AssessmentQuoteSummarySerializer(serializers.ModelSerializer):
    completion_percentage = serializers.SerializerMethodField()
    best_provider_total = serializers.SerializerMethodField()
    assessment_info = serializers.SerializerMethodField()
    provider_totals = serializers.SerializerMethodField()
    
    class Meta:
        model = AssessmentQuoteSummary
        fields = '__all__'
        read_only_fields = ('created_date', 'last_updated')
    
    def get_completion_percentage(self, obj):
        return obj.calculate_completion_percentage()
    
    def get_best_provider_total(self, obj):
        return obj.get_best_provider_total()
    
    def get_assessment_info(self, obj):
        return {
            'assessment_id': obj.assessment.assessment_id,
            'vehicle_make': obj.assessment.vehicle.make,
            'vehicle_model': obj.assessment.vehicle.model,
            'status': obj.assessment.status
        }
    
    def get_provider_totals(self, obj):
        return {
            'assessor': float(obj.assessor_total) if obj.assessor_total else None,
            'dealer': float(obj.dealer_total) if obj.dealer_total else None,
            'independent': float(obj.independent_total) if obj.independent_total else None,
            'network': float(obj.network_total) if obj.network_total else None
        }