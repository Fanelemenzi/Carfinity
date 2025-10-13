# Generated migration for onboarding workflow updates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0001_initial'),
    ]

    operations = [
        # Add status and completed_date fields to CustomerOnboarding
        migrations.AddField(
            model_name='customeronboarding',
            name='status',
            field=models.CharField(
                choices=[
                    ('in_progress', 'In Progress'),
                    ('completed', 'Completed'),
                    ('cancelled', 'Cancelled')
                ],
                default='in_progress',
                max_length=15
            ),
        ),
        migrations.AddField(
            model_name='customeronboarding',
            name='completed_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        # Rename completed_at to created_at for consistency
        migrations.RenameField(
            model_name='customeronboarding',
            old_name='completed_at',
            new_name='created_at',
        ),
        
        # Change VehicleOnboarding relationship to OneToOneField
        migrations.AlterField(
            model_name='vehicleonboarding',
            name='customer_onboarding',
            field=models.OneToOneField(
                on_delete=models.deletion.CASCADE,
                related_name='vehicle_onboarding',
                to='onboarding.customeronboarding'
            ),
        ),
        
        # Add indexes for better performance
        migrations.AddIndex(
            model_name='customeronboarding',
            index=models.Index(fields=['user', 'status'], name='onboarding_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='customeronboarding',
            index=models.Index(fields=['status', 'created_at'], name='onboarding_status_created_idx'),
        ),
        
        # Add Meta ordering
        migrations.AlterModelOptions(
            name='customeronboarding',
            options={'ordering': ['-created_at']},
        ),
    ]