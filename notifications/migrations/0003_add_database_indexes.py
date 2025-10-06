# Generated manually for database index optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS notifications_vehiclealert_vehicle_is_active_idx ON notifications_vehiclealert (vehicle_id, is_active);",
            reverse_sql="DROP INDEX IF EXISTS notifications_vehiclealert_vehicle_is_active_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS notifications_vehiclealert_vehicle_type_active_idx ON notifications_vehiclealert (vehicle_id, alert_type, is_active);",
            reverse_sql="DROP INDEX IF EXISTS notifications_vehiclealert_vehicle_type_active_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS notifications_vehiclealert_priority_created_idx ON notifications_vehiclealert (priority, created_at);",
            reverse_sql="DROP INDEX IF EXISTS notifications_vehiclealert_priority_created_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS notifications_vehiclealert_active_created_idx ON notifications_vehiclealert (is_active, created_at);",
            reverse_sql="DROP INDEX IF EXISTS notifications_vehiclealert_active_created_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS notifications_vehiclecostanalytics_vehicle_month_idx ON notifications_vehiclecostanalytics (vehicle_id, month);",
            reverse_sql="DROP INDEX IF EXISTS notifications_vehiclecostanalytics_vehicle_month_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS notifications_vehiclecostanalytics_month_idx ON notifications_vehiclecostanalytics (month);",
            reverse_sql="DROP INDEX IF EXISTS notifications_vehiclecostanalytics_month_idx;"
        ),
    ]