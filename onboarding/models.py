from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from datetime import date

# Create your models here.

class PendingVehicleOnboarding(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # Who submitted the onboarding request
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pending_vehicle_onboardings')
    # Which client is this for
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pending_client_vehicles')
    # Data fields (store as JSON for flexibility)
    vehicle_data = models.JSONField()
    ownership_data = models.JSONField()
    status_data = models.JSONField()
    history_data = models.JSONField(blank=True, null=True)
    equipment_data = models.JSONField()
    # New field for image data
    image_data = models.JSONField(blank=True, null=True, help_text="Stores image URLs and metadata")
    # Approval status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_vehicle_onboardings')

    def __str__(self):
        return f"Pending Vehicle for {self.client.username} (by {self.submitted_by.username if self.submitted_by else 'Unknown'})"


class CustomerOnboarding(models.Model):
    """Main onboarding questionnaire for new customers"""
    
    # User relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Personal Information
    CUSTOMER_TYPE_CHOICES = [
        ('individual', 'Individual Owner'),
        ('small_business', 'Small Business (2-10 vehicles)'),
        ('medium_business', 'Medium Business (11-50 vehicles)'),
        ('large_fleet', 'Large Fleet (50+ vehicles)'),
    ]
    customer_type = models.CharField(
        max_length=20, choices=CUSTOMER_TYPE_CHOICES,help_text="What type of customer are you?")
    
    # Contact preferences
    COMMUNICATION_PREFERENCES = [
        ('email', 'Email'),
        ('sms', 'SMS/Text'),
        ('phone', 'Phone Call'),
        ('app_notification', 'In-App Notification'),
    ]
    preferred_communication = models.CharField(max_length=20, choices=COMMUNICATION_PREFERENCES, default='email', help_text="How would you prefer to receive maintenance reminders?")
    
    # Service preferences
    REMINDER_FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    reminder_frequency = models.CharField(max_length=15, choices=REMINDER_FREQUENCY_CHOICES, default='monthly',  help_text="How often would you like maintenance reminders?")
    
    # Service area and preferences
    SERVICE_RADIUS_CHOICES = [
        ('5', 'Within 5 miles'),
        ('10', 'Within 10 miles'),
        ('15', 'Within 15 miles'),
        ('25', 'Within 25 miles'),
        ('50', 'Within 50 miles'),
    ]
    service_radius = models.CharField(max_length=5,choices=SERVICE_RADIUS_CHOICES, help_text="How far are you willing to travel for service, or have mobile service come to you?")
    
    # Budget and service level
    MONTHLY_BUDGET_CHOICES = [
        ('under_50', 'Under $50/month'),
        ('50_100', '$50-100/month'),
        ('100_200', '$100-200/month'),
        ('200_500', '$200-500/month'),
        ('over_500', 'Over $500/month'),
        ('as_needed', 'Pay as needed (no budget)'),
    ]
    monthly_maintenance_budget = models.CharField(max_length=15,choices=MONTHLY_BUDGET_CHOICES,help_text="What's your approximate monthly budget for vehicle maintenance?")
    
    # Service preferences
    mobile_service_interest = models.BooleanField(default=False,help_text="Are you interested in mobile mechanic services (we come to you)?")
    emergency_service_interest = models.BooleanField(default=False, help_text="Would you like 24/7 emergency roadside assistance?")
    
    # Experience level
    MAINTENANCE_EXPERIENCE_CHOICES = [
        ('beginner', 'Beginner - I know very little about car maintenance'),
        ('intermediate', 'Intermediate - I know basic maintenance'),
        ('advanced', 'Advanced - I do some repairs myself'),
        ('expert', 'Expert - I handle most maintenance myself'),
    ]
    
    maintenance_knowledge = models.CharField(max_length=15, choices=MAINTENANCE_EXPERIENCE_CHOICES, help_text="How would you describe your car maintenance knowledge?")
    
    # Previous service history
    current_mechanic = models.CharField(max_length=200, blank=True, null=True, help_text="Do you currently have a trusted mechanic or service center? (Optional)")
    maintenance_tracking_method = models.CharField(max_length=200, blank=True, null=True, help_text="How do you currently track vehicle maintenance? (e.g., spreadsheet, app, paper records, don't track)")
    
    # Pain points
    biggest_maintenance_challenge = models.TextField(blank=True,null=True,help_text="What's your biggest challenge with vehicle maintenance? (Optional)")
    
    # Goals
    MAINTENANCE_GOALS = [
        ('save_money', 'Save money on repairs'),
        ('extend_vehicle_life', 'Extend vehicle lifespan'),
        ('avoid_breakdowns', 'Avoid unexpected breakdowns'),
        ('maintain_warranty', 'Maintain warranty coverage'),
        ('improve_safety', 'Improve vehicle safety'),
        ('better_fuel_economy', 'Improve fuel economy'),
        ('convenience', 'Make maintenance more convenient'),
    ]
    
    primary_goal = models.CharField(max_length=25,choices=MAINTENANCE_GOALS,help_text="What's your primary goal for vehicle maintenance?")
    
    # Service Preferences & Budget (from image 1)
    SERVICE_PRIORITY_CHOICES = [
        ('convenience', 'Convenience'),
        ('cost', 'Cost'),
        ('service_quality', 'Service Quality'),
    ]
    
    service_priority = models.CharField(max_length=15,choices=SERVICE_PRIORITY_CHOICES,help_text="What's most important to you: convenience, cost, or service quality?")
    
    PAYMENT_MODEL_CHOICES = [
        ('subscription', 'Subscription maintenance plans'),
        ('pay_per_service', 'Pay-per-service'),
        ('both', 'Both options interest me'),
    ]
    
    preferred_payment_model = models.CharField(max_length=20,choices=PAYMENT_MODEL_CHOICES,help_text="Are you interested in subscription maintenance plans or pay-per-service?")
    
    PARTS_PREFERENCE_CHOICES = [
        ('oem_only', 'OEM parts only'),
        ('quality_aftermarket', 'Quality aftermarket parts acceptable'),
        ('cost_effective', 'Most cost-effective option'),
    ]
    
    parts_preference = models.CharField(max_length=20,choices=PARTS_PREFERENCE_CHOICES,help_text="Do you prefer OEM parts or are quality aftermarket parts acceptable?")
    
    # Insurance & Warranty Information (from image 2)
    auto_insurance_provider = models.CharField(max_length=100,blank=True,null=True,help_text="Who is your current auto insurance provider?")
    vehicle_under_warranty = models.BooleanField(default=False,help_text="Is your vehicle still under manufacturer warranty?")
    
    EXTENDED_WARRANTY_INTEREST_CHOICES = [
        ('very_interested', 'Very interested'),
        ('somewhat_interested', 'Somewhat interested'),
        ('not_interested', 'Not interested'),
        ('already_have', 'Already have extended warranty/service protection'),
    ]
    
    extended_warranty_interest = models.CharField(max_length=20,choices=EXTENDED_WARRANTY_INTEREST_CHOICES,help_text="Are you interested in extended warranty or service protection plans?")
    
    # Referral & Growth (from image 2)
    REFERRAL_SOURCE_CHOICES = [
        ('google_search', 'Google search'),
        ('social_media', 'Social media'),
        ('friend_family', 'Friend or family member'),
        ('online_ad', 'Online advertisement'),
        ('mechanic_referral', 'Mechanic referral'),
        ('app_store', 'App store'),
        ('other', 'Other'),
    ]
    
    how_heard_about_service = models.CharField(max_length=20,choices=REFERRAL_SOURCE_CHOICES,help_text="How did you hear about our service?")
    potential_referrals = models.BooleanField(default=False,help_text="Do you know others who might benefit from our services?")
    interested_in_referral_rewards = models.BooleanField(default=False,help_text="Would you be interested in earning referral rewards?")
    
    # Onboarding completion
    completed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Onboarding - {self.user.username} ({self.customer_type})"

class VehicleOnboarding(models.Model):
    """Vehicle-specific onboarding questions - can have multiple vehicles per customer"""
    
    customer_onboarding = models.ForeignKey(CustomerOnboarding, on_delete=models.CASCADE, related_name='vehicles')
    
    # Basic vehicle information
    vin_number = models.CharField(
        max_length=17,
        validators=[RegexValidator(r'^[A-HJ-NPR-Z0-9]{17}$', 'Enter a valid 17-character VIN')],
        help_text="Vehicle Identification Number (17 characters)"
    )
    
    # If VIN lookup fails, manual entry
    make = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Vehicle make (e.g., Toyota, Ford)"
    )
    
    model = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Vehicle model (e.g., Camry, F-150)"
    )
    
    year = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2030)],
        blank=True,
        null=True,
        help_text="Model year"
    )
    
    # Vehicle usage patterns
    USAGE_TYPE_CHOICES = [
        ('daily_commute', 'Daily commuting'),
        ('weekend_only', 'Weekend/recreational use'),
        ('business', 'Business/work vehicle'),
        ('family_trips', 'Family trips and errands'),
        ('delivery', 'Delivery/commercial use'),
        ('emergency_only', 'Emergency/backup vehicle'),
    ]
    
    primary_usage = models.CharField(
        max_length=20,
        choices=USAGE_TYPE_CHOICES,
        help_text="How do you primarily use this vehicle?"
    )
    
    # Mileage information
    current_odometer = models.PositiveIntegerField(
        help_text="Current odometer reading (miles)"
    )
    
    ANNUAL_MILEAGE_CHOICES = [
        ('under_5k', 'Under 5,000 miles/year'),
        ('5k_10k', '5,000-10,000 miles/year'),
        ('10k_15k', '10,000-15,000 miles/year'),
        ('15k_20k', '15,000-20,000 miles/year'),
        ('20k_25k', '20,000-25,000 miles/year'),
        ('over_25k', 'Over 25,000 miles/year'),
    ]
    
    estimated_annual_mileage = models.CharField(
        max_length=10,
        choices=ANNUAL_MILEAGE_CHOICES,
        help_text="Approximately how many miles do you drive this vehicle per year?"
    )
    
    # Driving conditions
    DRIVING_CONDITIONS = [
        ('city_mostly', 'Mostly city/stop-and-go traffic'),
        ('highway_mostly', 'Mostly highway/long distance'),
        ('mixed', 'Mixed city and highway'),
        ('rural', 'Rural/country roads'),
        ('harsh', 'Harsh conditions (extreme weather, mountains, towing)'),
    ]
    
    typical_driving_conditions = models.CharField(
        max_length=15,
        choices=DRIVING_CONDITIONS,
        help_text="What describes your typical driving conditions?"
    )
    
    # Current vehicle condition
    VEHICLE_CONDITION_CHOICES = [
        ('excellent', 'Excellent - Like new'),
        ('good', 'Good - Well maintained'),
        ('fair', 'Fair - Some issues but runs well'),
        ('poor', 'Poor - Frequent problems'),
        ('unknown', 'Unknown - Recently acquired'),
    ]
    
    current_condition = models.CharField(
        max_length=10,
        choices=VEHICLE_CONDITION_CHOICES,
        help_text="How would you describe the current condition of this vehicle?"
    )
    
    # Recent service history
    last_oil_change = models.DateField(
        blank=True,
        null=True,
        help_text="When was the last oil change? (Optional if unknown)"
    )
    
    last_major_service = models.DateField(
        blank=True,
        null=True,
        help_text="When was the last major service/tune-up? (Optional if unknown)"
    )
    
    # Known issues
    current_problems = models.TextField(
        blank=True,
        null=True,
        help_text="Are there any current problems or concerns with this vehicle? (Optional)"
    )
    
    # Warranty information
    under_warranty = models.BooleanField(
        default=False,
        help_text="Is this vehicle currently under manufacturer warranty?"
    )
    
    warranty_expires = models.DateField(
        blank=True,
        null=True,
        help_text="When does the warranty expire? (If applicable)"
    )
    
    # Service preferences for this vehicle
    MAINTENANCE_PRIORITY_CHOICES = [
        ('cost_effective', 'Most cost-effective options'),
        ('oem_parts', 'OEM parts and dealer service'),
        ('performance', 'Performance and reliability focused'),
        ('eco_friendly', 'Environmentally conscious options'),
        ('quick_turnaround', 'Fastest service possible'),
    ]
    
    maintenance_preference = models.CharField(
        max_length=20,
        choices=MAINTENANCE_PRIORITY_CHOICES,
        help_text="What's most important for maintaining this vehicle?"
    )
    
    # Vehicle nickname (for multi-vehicle households)
    vehicle_nickname = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Optional nickname for this vehicle (e.g., 'Work Truck', 'Family Car')"
    )
    
    # Timestamps
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model} - {self.vehicle_nickname or 'Vehicle'}"
    
    class Meta:
        unique_together = ['customer_onboarding', 'vin_number']
