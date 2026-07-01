from django.apps import AppConfig


class PathologyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pathology'
    verbose_name = 'Pathology Laboratory Management'

    def ready(self):
        import pathology.signals
