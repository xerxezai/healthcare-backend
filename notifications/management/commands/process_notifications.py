# backend/notifications/management/commands/process_notifications.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.services import NotificationService
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process pending notifications from the queue'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of notifications to process per batch'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Interval in seconds between processing batches (for continuous mode)'
        )
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run continuously, processing notifications at regular intervals'
        )
        parser.add_argument(
            '--max-iterations',
            type=int,
            default=0,
            help='Maximum number of iterations in continuous mode (0 = unlimited)'
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        interval = options['interval']
        continuous = options['continuous']
        max_iterations = options['max_iterations']
        
        service = NotificationService()
        iteration = 0
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting notification processor...')
        )
        
        if continuous:
            self.stdout.write(
                self.style.WARNING(
                    f'Running in continuous mode with {interval}s intervals'
                )
            )
        
        try:
            while True:
                iteration += 1
                start_time = timezone.now()
                
                self.stdout.write(f'\nProcessing batch {iteration}...')
                
                # Process notifications
                results = service.process_queue(limit=limit)
                
                processing_time = (timezone.now() - start_time).total_seconds()
                
                # Display results
                if results['processed'] > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Processed {results["processed"]} notifications '
                            f'in {processing_time:.2f}s'
                        )
                    )
                
                if results['failed'] > 0:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Failed to process {results["failed"]} notifications'
                        )
                    )
                
                if results['processed'] == 0 and results['failed'] == 0:
                    self.stdout.write(
                        self.style.WARNING('📭 No notifications to process')
                    )
                
                # Check if we should continue
                if not continuous:
                    break
                
                if max_iterations > 0 and iteration >= max_iterations:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Reached maximum iterations ({max_iterations}). Stopping.'
                        )
                    )
                    break
                
                # Wait for next iteration
                self.stdout.write(f'Waiting {interval}s for next batch...')
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nReceived interrupt signal. Shutting down gracefully...')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error in notification processor: {str(e)}')
            )
            logger.error(f'Error in notification processor: {str(e)}', exc_info=True)
        
        self.stdout.write(
            self.style.SUCCESS(f'Notification processor stopped after {iteration} iterations.')
        )
