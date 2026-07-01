"""
Manual Billing App Configuration
"""

from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billing'
    verbose_name = 'Manual Billing System'
    
    def ready(self):
        """
        Import signals when the app is ready
        """
        try:
            import billing.signals
        except ImportError:
            pass
