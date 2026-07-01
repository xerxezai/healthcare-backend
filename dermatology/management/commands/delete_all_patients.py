from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dermatology.models import Patient
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Delete all dermatology patients and their associated user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all patient data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL dermatology patients and their user accounts.\n'
                    'Run with --confirm to proceed.'
                )
            )
            return

        try:
            with transaction.atomic():
                # Get all dermatology patients
                patients = Patient.objects.all()
                patient_count = patients.count()
                
                self.stdout.write(f'Found {patient_count} dermatology patients to delete.')
                
                # Get associated users
                user_ids = list(patients.values_list('user_id', flat=True))
                
                # Delete patients (this will cascade to related records)
                patients.delete()
                
                # Delete associated user accounts (only those that were dermatology patients)
                deleted_users = User.objects.filter(id__in=user_ids).delete()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully deleted {patient_count} dermatology patients '
                        f'and {deleted_users[0]} user accounts.'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error deleting patients: {str(e)}')
            )
