# Generated manually to fix due_mileage constraint issue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('insurance_app', '0002_insurancepolicy_organization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maintenanceschedule',
            name='due_mileage',
            field=models.IntegerField(default=0, help_text='Mileage when maintenance is due'),
        ),
    ]