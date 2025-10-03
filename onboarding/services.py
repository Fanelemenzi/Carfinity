"""
Onboarding services for user workflow and dashboard assignment.
"""

from typing import Optional
from django.contrib.auth.models import User, Group
from django.shortcuts import reverse
import logging

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Service class to handle onboarding workflow and dashboard assignment.
    """
    
    @classmethod
    def assign_user_dashboard(cls, user: User) -> str:
        """
        Assign appropriate dashboard to user after onboarding completion.
        
        This method determines which dashboard the user should be redirected to
        based on their profile, groups, or default assignment logic.
        
        Args:
            user: Django User instance
            
        Returns:
            Dashboard URL string
        """
        logger.info(f"Assigning dashboard for user {user.id} ({user.username})")
        
        try:
            # Check if user already has group assignments
            user_groups = list(user.groups.values_list('name', flat=True))
            logger.info(f"User {user.id} current groups: {user_groups}")
            
            if user_groups:
                # User already has groups, use existing dashboard routing
                from users.services import AuthenticationService
                return AuthenticationService.get_redirect_url_after_login(user)
            
            # For new users without group assignments, assign default group and dashboard
            return cls._assign_default_dashboard(user)
            
        except Exception as e:
            logger.error(f"Error assigning dashboard for user {user.id}: {str(e)}")
            # Fallback to general dashboard
            return '/dashboard/'
    
    @classmethod
    def _assign_default_dashboard(cls, user: User) -> str:
        """
        Assign default dashboard for new users without group assignments.
        
        Args:
            user: Django User instance
            
        Returns:
            Dashboard URL string
        """
        try:
            # Get user's onboarding data to determine appropriate dashboard
            from .models import CustomerOnboarding
            
            try:
                customer_onboarding = CustomerOnboarding.objects.get(user=user)
                dashboard_assignment = cls._determine_dashboard_from_onboarding(customer_onboarding)
                
                if dashboard_assignment:
                    group_name, dashboard_url = dashboard_assignment
                    
                    # Assign user to the appropriate group
                    group, created = Group.objects.get_or_create(name=group_name)
                    user.groups.add(group)
                    
                    logger.info(f"Assigned user {user.id} to group '{group_name}' with dashboard '{dashboard_url}'")
                    return dashboard_url
                    
            except CustomerOnboarding.DoesNotExist:
                logger.warning(f"No onboarding data found for user {user.id}")
            
            # Default assignment for users without specific onboarding data
            return cls._assign_default_group_and_dashboard(user)
            
        except Exception as e:
            logger.error(f"Error in default dashboard assignment for user {user.id}: {str(e)}")
            return '/dashboard/'
    
    @classmethod
    def _determine_dashboard_from_onboarding(cls, customer_onboarding) -> Optional[tuple]:
        """
        Determine appropriate dashboard based on onboarding responses.
        
        Args:
            customer_onboarding: CustomerOnboarding instance
            
        Returns:
            Tuple of (group_name, dashboard_url) or None
        """
        try:
            # Log onboarding data for reference but assign all users to AutoCare
            customer_type = customer_onboarding.customer_type
            maintenance_knowledge = customer_onboarding.maintenance_knowledge
            primary_goal = customer_onboarding.primary_goal
            
            logger.info(f"Processing onboarding for customer_type: {customer_type}, "
                       f"maintenance_knowledge: {maintenance_knowledge}, primary_goal: {primary_goal}")
            
            # Assign all users to AutoCare dashboard regardless of responses
            logger.info("Assigning AutoCare dashboard (default for all users)")
            return ('AutoCare', '/maintenance/dashboard/')
            
        except Exception as e:
            logger.error(f"Error determining dashboard from onboarding: {str(e)}")
            return None
    
    @classmethod
    def _assign_default_group_and_dashboard(cls, user: User) -> str:
        """
        Assign default group and dashboard for users without onboarding data.
        
        Args:
            user: Django User instance
            
        Returns:
            Dashboard URL string
        """
        try:
            # Default new users to AutoCare group
            autocare_group, created = Group.objects.get_or_create(name='AutoCare')
            user.groups.add(autocare_group)
            
            logger.info(f"Assigned default AutoCare group to user {user.id}")
            return '/maintenance/dashboard/'
            
        except Exception as e:
            logger.error(f"Error assigning default group to user {user.id}: {str(e)}")
            return '/dashboard/'
    
    @classmethod
    def check_onboarding_completion(cls, user: User) -> bool:
        """
        Check if user has completed the onboarding process.
        
        Args:
            user: Django User instance
            
        Returns:
            Boolean indicating if onboarding is complete
        """
        try:
            from .models import CustomerOnboarding
            CustomerOnboarding.objects.get(user=user)
            return True
        except CustomerOnboarding.DoesNotExist:
            return False
    
    @classmethod
    def get_onboarding_progress(cls, user: User) -> dict:
        """
        Get user's onboarding progress information.
        
        Args:
            user: Django User instance
            
        Returns:
            Dictionary with onboarding progress details
        """
        try:
            from .models import CustomerOnboarding, VehicleOnboarding
            
            progress = {
                'completed': False,
                'customer_info': False,
                'vehicle_info': False,
                'dashboard_assigned': False,
                'next_step': 'onboarding:onboarding_step_1'
            }
            
            try:
                customer_onboarding = CustomerOnboarding.objects.get(user=user)
                progress['customer_info'] = True
                
                # Check for vehicle information
                vehicle_count = VehicleOnboarding.objects.filter(
                    customer_onboarding=customer_onboarding
                ).count()
                
                if vehicle_count > 0:
                    progress['vehicle_info'] = True
                
                # Check if user has group assignments (dashboard assigned)
                if user.groups.exists():
                    progress['dashboard_assigned'] = True
                    progress['completed'] = True
                    progress['next_step'] = 'dashboard'
                else:
                    progress['next_step'] = 'onboarding:onboarding_complete'
                    
            except CustomerOnboarding.DoesNotExist:
                progress['next_step'] = 'onboarding:onboarding_step_1'
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting onboarding progress for user {user.id}: {str(e)}")
            return {
                'completed': False,
                'customer_info': False,
                'vehicle_info': False,
                'dashboard_assigned': False,
                'next_step': 'onboarding:onboarding_step_1'
            }