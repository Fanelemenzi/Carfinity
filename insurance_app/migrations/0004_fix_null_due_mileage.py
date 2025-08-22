# Generated manually to fix null due_mileage values

from django.db import migrations


def fix_null_due_mileage(apps, schema_editor):
    """Fix any existing MaintenanceSchedule records with null due_mileage"""
    MaintenanceSchedule = apps.get_model('insurance_app', 'MaintenanceSchedule')
    
    # Update any records with null due_mileage to 0
    MaintenanceSchedule.objects.filter(due_mileage__isnull=True).update(due_mileage=0)


def reverse_fix_null_due_mileage(apps, schema_editor):
    """Reverse operation - no action needed"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('insurance_app', '0003_add_due_mileage_default'),
    ]

    operations = [
        migrations.RunPython(fix_null_due_mileage, reverse_fix_null_due_mileage),
    ]