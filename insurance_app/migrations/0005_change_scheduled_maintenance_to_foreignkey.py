# Generated manually to change OneToOneField to ForeignKey

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0001_initial'),  # Adjust this to match your maintenance app's latest migration
        ('insurance_app', '0004_fix_null_due_mileage'),
    ]

    operations = [
        # Remove the old OneToOneField constraint
        migrations.AlterField(
            model_name='maintenanceschedule',
            name='scheduled_maintenance',
            field=models.ForeignKey(
                blank=True,
                help_text='Link to the maintenance app scheduled maintenance',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='insurance_schedules',
                to='maintenance.scheduledmaintenance'
            ),
        ),
    ]