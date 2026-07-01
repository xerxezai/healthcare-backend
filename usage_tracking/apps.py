from django.apps import AppConfig


class UsageTrackingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usage_tracking'
    verbose_name = 'Usage Tracking'
    
    def ready(self):
        # Import signals when app is ready
        # import usage_tracking.signals  # TODO: Add signals if needed
        pass
