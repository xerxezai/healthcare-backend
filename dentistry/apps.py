from django.apps import AppConfig


class DentistryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dentistry'
    verbose_name = 'Dental Management System'

    def ready(self):
        import dentistry.signals
