from django.apps import AppConfig


class DermatologyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dermatology'
    verbose_name = 'Dermatology Department'

    def ready(self):
        import dermatology.signals
