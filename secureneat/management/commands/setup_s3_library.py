from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import sys
import os

class Command(BaseCommand):
    help = 'Setup S3 Library folder structure and optionally upload sample content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-samples',
            action='store_true',
            help='Upload sample content for testing',
        )

    def handle(self, *args, **options):
        # Import here to avoid Django setup issues
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        try:
            from setup_s3_library import setup_s3_library_structure, upload_sample_content
            
            self.stdout.write(
                self.style.SUCCESS('Starting S3 Library setup...')
            )
            
            # Setup folder structure
            if setup_s3_library_structure():
                self.stdout.write(
                    self.style.SUCCESS('✅ S3 folder structure created successfully!')
                )
            
            # Upload sample content if requested
            if options['with_samples']:
                self.stdout.write('Uploading sample content...')
                upload_sample_content()
                self.stdout.write(
                    self.style.SUCCESS('✅ Sample content uploaded successfully!')
                )
            
            self.stdout.write(
                self.style.SUCCESS('\n🎉 S3 Library setup complete!')
            )
            self.stdout.write(
                'You can now access your library at: http://localhost:5173/SecureNeat/mcq-practice (Cloud Library tab)'
            )
            
        except Exception as e:
            raise CommandError(f'Setup failed: {e}')
