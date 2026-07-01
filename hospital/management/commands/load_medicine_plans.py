from django.core.management.base import BaseCommand
from django.core.management import call_command
import os

class Command(BaseCommand):
    help = 'Load updated subscription plans with medicine services'

    def handle(self, *args, **options):
        try:
            self.stdout.write('🔄 Loading updated subscription plans with medicine services...')
            
            # Load the updated subscription plans
            fixtures_path = os.path.join('load', 'subscription_plans_updated.json')
            
            self.stdout.write(f'📁 Loading from: {fixtures_path}')
            call_command('loaddata', fixtures_path)
            
            self.stdout.write(self.style.SUCCESS('✅ Updated subscription plans loaded successfully!'))
            self.stdout.write('')
            self.stdout.write('📋 New Plans Available:')
            self.stdout.write('  1. SecureNeat - AI chatbot and MCQ generation')
            self.stdout.write('  2. 💊 Medicine Professional - Medicine management + AI + Analytics')
            self.stdout.write('  3. Radiology - Radiology report analysis')  
            self.stdout.write('  4. Full Admin Access - All features included')
            self.stdout.write('')
            self.stdout.write('🎯 Medicine services now available:')
            self.stdout.write('  • Medicine Management Suite')
            self.stdout.write('  • Diabetes Management AI')
            self.stdout.write('  • Prescription Analytics')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error loading subscription plans: {str(e)}'))
            self.stdout.write('💡 Make sure the backend server is running and database is accessible')
