from django.apps import AppConfig


class InsuranceAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "insurance_app"
    
    def ready(self):
        import insurance_app.signals
