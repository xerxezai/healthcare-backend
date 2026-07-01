from django.apps import AppConfig


class NetflixConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'netflix'
    verbose_name = 'Netflix-like Content Management'
    
    def ready(self):
        # Import signal handlers
        try:
            import netflix.signals
        except ImportError:
            pass
