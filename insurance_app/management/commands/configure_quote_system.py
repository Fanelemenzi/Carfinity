"""
Management command for configuring the quote system settings.
This command allows administrators to update system configuration from the command line.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from decimal import Decimal

from insurance_app.models import QuoteSystemConfiguration, ProviderConfiguration, QuoteSystemAuditLog

class Command(BaseCommand):
    help = 'Configure quote system settings and provider configurations'
    
    def add_arguments(self, parser):
        # System configuration options
        parser.add_argument(
            '--labor-rate',
            type=float,
            help='Set default labor rate (GBP per hour)'
        )
        parser.add_argument(
            '--paint-percentage',
            type=float,
            help='Set paint cost percentage for body panels'
        )
        parser.add_argument(
            '--quote-expiry-days',
            type=int,
            help='Set default quote expiry period in days'
        )
        parser.add_argument(
            '--confidence-threshold',
            type=int,
            help='Set minimum confidence threshold for market averages (0-100)'
        )
        
        # Provider enable/disable options
        parser.add_argument(
            '--enable-assessor',
            action='store_true',
            help='Enable assessor estimates'
        )
        parser.add_argument(
            '--disable-assessor',
            action='store_true',
            help='Disable assessor estimates'
        )
        parser.add_argument(
            '--enable-dealer',
            action='store_true',
            help='Enable dealer quotes'
        )
        parser.add_argument(
            '--disable-dealer',
            action='store_true',
            help='Disable dealer quotes'
        )
        parser.add_argument(
            '--enable-independent',
            action='store_true',
            help='Enable independent garage quotes'
        )
        parser.add_argument(
            '--disable-independent',
            action='store_true',
            help='Disable independent garage quotes'
        )
        parser.add_argument(
            '--enable-network',
            action='store_true',
            help='Enable insurance network quotes'
        )
        parser.add_argument(
            '--disable-network',
            action='store_true',
            help='Disable insurance network quotes'
        )
        
        # Recommendation weights
        parser.add_argument(
            '--price-weight',
            type=float,
            help='Set price weight for recommendations (0.0-1.0)'
        )
        parser.add_argument(
            '--quality-weight',
            type=float,
            help='Set quality weight for recommendations (0.0-1.0)'
        )
        parser.add_argument(
            '--timeline-weight',
            type=float,
            help='Set timeline weight for recommendations (0.0-1.0)'
        )
        
        # Provider configuration
        parser.add_argument(
            '--provider-type',
            choices=['assessor', 'dealer', 'independent', 'network'],
            help='Provider type to configure'
        )
        parser.add_argument(
            '--api-endpoint',
            help='Set API endpoint for provider (use with --provider-type)'
        )
        parser.add_argument(
            '--api-key',
            help='Set API key for provider (use with --provider-type)'
        )
        parser.add_argument(
            '--reliability-score',
            type=int,
            help='Set reliability score for provider 0-100 (use with --provider-type)'
        )
        
        # Utility options
        parser.add_argument(
            '--show-config',
            action='store_true',
            help='Display current configuration'
        )
        parser.add_argument(
            '--reset-defaults',
            action='store_true',
            help='Reset configuration to default values'
        )
        parser.add_argument(
            '--user',
            help='Username of the user making changes (for audit log)'
        )
    
    def handle(self, *args, **options):
        # Get or create configuration
        config = QuoteSystemConfiguration.get_config()
        
        # Get user for audit logging
        user = None
        if options['user']:
            try:
                user = User.objects.get(username=options['user'])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'User "{options["user"]}" not found. Changes will be logged without user.')
                )
        
        # Show current configuration if requested
        if options['show_config']:
            self.show_current_configuration(config)
            return
        
        # Reset to defaults if requested
        if options['reset_defaults']:
            self.reset_to_defaults(config, user)
            return
        
        # Track changes for audit log
        changes_made = []
        
        # Update system configuration
        changes_made.extend(self.update_system_config(config, options))
        
        # Update provider configurations
        if options['provider_type']:
            changes_made.extend(self.update_provider_config(options))
        
        # Save configuration with user info
        if changes_made:
            config.updated_by = user
            config.save()
            
            # Log changes
            self.log_configuration_changes(changes_made, user)
            
            self.stdout.write(
                self.style.SUCCESS(f'Configuration updated successfully. {len(changes_made)} changes made.')
            )
            
            # Show updated configuration
            self.show_current_configuration(config)
        else:
            self.stdout.write(self.style.WARNING('No configuration changes specified.'))
    
    def update_system_config(self, config, options):
        """Update system configuration settings"""
        changes = []
        
        # Labor rate
        if options['labor_rate'] is not None:
            old_value = float(config.default_labor_rate)
            config.default_labor_rate = Decimal(str(options['labor_rate']))
            changes.append(f"Labor rate: £{old_value:.2f} → £{options['labor_rate']:.2f}")
        
        # Paint percentage
        if options['paint_percentage'] is not None:
            old_value = float(config.paint_cost_percentage)
            config.paint_cost_percentage = Decimal(str(options['paint_percentage']))
            changes.append(f"Paint percentage: {old_value:.1f}% → {options['paint_percentage']:.1f}%")
        
        # Quote expiry days
        if options['quote_expiry_days'] is not None:
            old_value = config.default_quote_expiry_days
            config.default_quote_expiry_days = options['quote_expiry_days']
            changes.append(f"Quote expiry: {old_value} days → {options['quote_expiry_days']} days")
        
        # Confidence threshold
        if options['confidence_threshold'] is not None:
            if not 0 <= options['confidence_threshold'] <= 100:
                raise CommandError('Confidence threshold must be between 0 and 100')
            old_value = config.confidence_threshold
            config.confidence_threshold = options['confidence_threshold']
            changes.append(f"Confidence threshold: {old_value}% → {options['confidence_threshold']}%")
        
        # Provider enable/disable
        provider_changes = self.update_provider_settings(config, options)
        changes.extend(provider_changes)
        
        # Recommendation weights
        weight_changes = self.update_recommendation_weights(config, options)
        changes.extend(weight_changes)
        
        return changes
    
    def update_provider_settings(self, config, options):
        """Update provider enable/disable settings"""
        changes = []
        
        providers = [
            ('assessor', 'enable_assessor_estimates', 'Assessor estimates'),
            ('dealer', 'enable_dealer_quotes', 'Dealer quotes'),
            ('independent', 'enable_independent_quotes', 'Independent quotes'),
            ('network', 'enable_network_quotes', 'Network quotes')
        ]
        
        for provider_key, config_field, display_name in providers:
            enable_key = f'enable_{provider_key}'
            disable_key = f'disable_{provider_key}'
            
            if options[enable_key]:
                if not getattr(config, config_field):
                    setattr(config, config_field, True)
                    changes.append(f"{display_name}: Disabled → Enabled")
            
            if options[disable_key]:
                if getattr(config, config_field):
                    setattr(config, config_field, False)
                    changes.append(f"{display_name}: Enabled → Disabled")
        
        return changes
    
    def update_recommendation_weights(self, config, options):
        """Update recommendation engine weights"""
        changes = []
        
        weights = [
            ('price_weight', 'Price weight'),
            ('quality_weight', 'Quality weight'),
            ('timeline_weight', 'Timeline weight')
        ]
        
        for weight_field, display_name in weights:
            if options[weight_field] is not None:
                if not 0.0 <= options[weight_field] <= 1.0:
                    raise CommandError(f'{display_name} must be between 0.0 and 1.0')
                
                old_value = float(getattr(config, weight_field))
                setattr(config, weight_field, Decimal(str(options[weight_field])))
                changes.append(f"{display_name}: {old_value:.2f} → {options[weight_field]:.2f}")
        
        return changes
    
    def update_provider_config(self, options):
        """Update individual provider configuration"""
        changes = []
        provider_type = options['provider_type']
        
        try:
            provider_config = ProviderConfiguration.objects.get(provider_type=provider_type)
        except ProviderConfiguration.DoesNotExist:
            provider_config = ProviderConfiguration.objects.create(provider_type=provider_type)
            changes.append(f"Created configuration for {provider_type} provider")
        
        # API endpoint
        if options['api_endpoint']:
            old_value = provider_config.api_endpoint or 'None'
            provider_config.api_endpoint = options['api_endpoint']
            changes.append(f"{provider_type} API endpoint: {old_value} → {options['api_endpoint']}")
        
        # API key
        if options['api_key']:
            old_has_key = bool(provider_config.api_key)
            provider_config.api_key = options['api_key']
            status = "Updated" if old_has_key else "Set"
            changes.append(f"{provider_type} API key: {status}")
        
        # Reliability score
        if options['reliability_score'] is not None:
            if not 0 <= options['reliability_score'] <= 100:
                raise CommandError('Reliability score must be between 0 and 100')
            
            old_value = provider_config.reliability_score
            provider_config.reliability_score = options['reliability_score']
            changes.append(f"{provider_type} reliability: {old_value} → {options['reliability_score']}")
        
        if changes:
            provider_config.save()
        
        return changes
    
    def reset_to_defaults(self, config, user):
        """Reset configuration to default values"""
        # Delete existing configuration to trigger defaults
        config.delete()
        
        # Create new configuration with defaults
        new_config = QuoteSystemConfiguration.get_config()
        new_config.updated_by = user
        new_config.save()
        
        # Reset provider configurations
        ProviderConfiguration.objects.all().delete()
        
        # Create default provider configurations
        default_providers = [
            ('assessor', True, 85, 2.0),
            ('dealer', True, 75, 24.0),
            ('independent', True, 70, 12.0),
            ('network', True, 80, 6.0)
        ]
        
        for provider_type, enabled, reliability, response_time in default_providers:
            ProviderConfiguration.objects.create(
                provider_type=provider_type,
                is_enabled=enabled,
                reliability_score=reliability,
                average_response_time_hours=response_time
            )
        
        self.log_configuration_changes(['Reset all configurations to defaults'], user)
        
        self.stdout.write(self.style.SUCCESS('Configuration reset to defaults successfully.'))
        self.show_current_configuration(new_config)
    
    def show_current_configuration(self, config):
        """Display current configuration"""
        self.stdout.write(self.style.SUCCESS('\n=== CURRENT QUOTE SYSTEM CONFIGURATION ==='))
        
        self.stdout.write('\n--- Cost Calculation Settings ---')
        self.stdout.write(f'Labor Rate: £{config.default_labor_rate}/hour')
        self.stdout.write(f'Paint Cost Percentage: {config.paint_cost_percentage}%')
        self.stdout.write(f'Additional Cost Percentage: {config.additional_cost_percentage}%')
        
        self.stdout.write('\n--- Quote Request Settings ---')
        self.stdout.write(f'Default Expiry: {config.default_quote_expiry_days} days')
        self.stdout.write(f'Minimum Quotes Required: {config.minimum_quotes_required}')
        self.stdout.write(f'Confidence Threshold: {config.confidence_threshold}%')
        
        self.stdout.write('\n--- Provider Settings ---')
        providers = [
            ('Assessor Estimates', config.enable_assessor_estimates),
            ('Dealer Quotes', config.enable_dealer_quotes),
            ('Independent Quotes', config.enable_independent_quotes),
            ('Network Quotes', config.enable_network_quotes)
        ]
        
        for name, enabled in providers:
            status = "✓ Enabled" if enabled else "✗ Disabled"
            self.stdout.write(f'{name}: {status}')
        
        self.stdout.write('\n--- Recommendation Weights ---')
        total_weight = (
            config.price_weight + config.quality_weight + config.timeline_weight + 
            config.warranty_weight + config.reliability_weight
        )
        self.stdout.write(f'Price: {config.price_weight} ({float(config.price_weight)*100:.0f}%)')
        self.stdout.write(f'Quality: {config.quality_weight} ({float(config.quality_weight)*100:.0f}%)')
        self.stdout.write(f'Timeline: {config.timeline_weight} ({float(config.timeline_weight)*100:.0f}%)')
        self.stdout.write(f'Warranty: {config.warranty_weight} ({float(config.warranty_weight)*100:.0f}%)')
        self.stdout.write(f'Reliability: {config.reliability_weight} ({float(config.reliability_weight)*100:.0f}%)')
        self.stdout.write(f'Total Weight: {total_weight} (should be 1.00)')
        
        self.stdout.write('\n--- System Monitoring ---')
        self.stdout.write(f'Performance Logging: {"✓ Enabled" if config.enable_performance_logging else "✗ Disabled"}')
        self.stdout.write(f'Health Monitoring: {"✓ Enabled" if config.enable_health_monitoring else "✗ Disabled"}')
        self.stdout.write(f'Log Retention: {config.log_retention_days} days')
        
        self.stdout.write('\n--- Provider Configurations ---')
        provider_configs = ProviderConfiguration.objects.all().order_by('provider_type')
        
        if provider_configs.exists():
            for provider in provider_configs:
                status = "✓ Enabled" if provider.is_enabled else "✗ Disabled"
                api_status = "API Configured" if provider.api_endpoint else "No API"
                self.stdout.write(
                    f'{provider.get_provider_type_display()}: {status}, '
                    f'Reliability: {provider.reliability_score}/100, '
                    f'Response: {provider.average_response_time_hours}h, '
                    f'{api_status}'
                )
        else:
            self.stdout.write('No provider configurations found.')
        
        self.stdout.write(f'\nLast Updated: {config.updated_at}')
        if config.updated_by:
            self.stdout.write(f'Updated By: {config.updated_by.username}')
        
        self.stdout.write(self.style.SUCCESS('\n=== END CONFIGURATION ===\n'))
    
    def log_configuration_changes(self, changes, user):
        """Log configuration changes to audit log"""
        QuoteSystemAuditLog.objects.create(
            action_type='configuration_updated',
            severity='info',
            user=user,
            description=f'Quote system configuration updated: {"; ".join(changes)}',
            additional_data={'changes': changes},
            object_type='configuration',
            object_id='system'
        )