from django.test import TestCase
from django.contrib.auth.models import User
from .models import PendingVehicleOnboarding
from django.utils import timezone

# Create your tests here.

class PendingVehicleOnboardingModelTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staff', password='test', is_staff=True)
        self.client_user = User.objects.create_user(username='client', password='test')

    def test_create_pending_onboarding(self):
        onboarding = PendingVehicleOnboarding.objects.create(
            submitted_by=self.staff,
            client=self.client_user,
            vehicle_data={'vin': '123', 'make': 'Test', 'model': 'Car', 'manufacture_year': 2020},
            ownership_data={'start_date': '2023-01-01'},
            status_data={'accident_history': 'NHA'},
            equipment_data={},
        )
        self.assertEqual(onboarding.status, 'pending')
        self.assertEqual(onboarding.client, self.client_user)

    def test_admin_approve_action(self):
        onboarding = PendingVehicleOnboarding.objects.create(
            submitted_by=self.staff,
            client=self.client_user,
            vehicle_data={'vin': '123', 'make': 'Test', 'model': 'Car', 'manufacture_year': 2020},
            ownership_data={'start_date': '2023-01-01'},
            status_data={'accident_history': 'NHA'},
            equipment_data={},
        )
        onboarding.status = 'approved'
        onboarding.reviewed_by = self.staff
        onboarding.reviewed_at = timezone.now()
        onboarding.save()
        self.assertEqual(onboarding.status, 'approved')
        self.assertEqual(onboarding.reviewed_by, self.staff)
