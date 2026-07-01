from django.apps import AppConfig


class AllopathyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'allopathy'
    verbose_name = 'Allopathy Module'
    
    def ready(self):
        try:
            import allopathy.signals  # noqa F401
        except ImportError:
            pass
