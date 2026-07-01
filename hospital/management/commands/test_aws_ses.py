from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import boto3
from botocore.exceptions import ClientError

class Command(BaseCommand):
    help = 'Test AWS SES configuration and connectivity'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing AWS SES Configuration...'))
        
        # Test 1: Check settings
        self.stdout.write('\n1. Checking Email Backend Configuration:')
        self.stdout.write(f'   EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'   AWS_SES_REGION_NAME: {getattr(settings, "AWS_SES_REGION_NAME", "Not set")}')
        self.stdout.write(f'   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        # Test 2: Check AWS credentials
        self.stdout.write('\n2. Checking AWS Credentials:')
        try:
            session = boto3.Session()
            credentials = session.get_credentials()
            if credentials:
                self.stdout.write(self.style.SUCCESS('   ✅ AWS credentials found'))
                self.stdout.write(f'   Access Key: {credentials.access_key[:4]}****{credentials.access_key[-4:]}')
            else:
                self.stdout.write(self.style.ERROR('   ❌ AWS credentials not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error getting credentials: {e}'))
        
        # Test 3: Test SES service connection
        self.stdout.write('\n3. Testing SES Service Connection:')
        try:
            ses_client = boto3.client('ses', region_name=getattr(settings, 'AWS_SES_REGION_NAME', 'ap-south-1'))
            response = ses_client.describe_account_sending_enabled()
            self.stdout.write(self.style.SUCCESS(f'   ✅ SES connection successful'))
            self.stdout.write(f'   Sending enabled: {response.get("Enabled", "Unknown")}')
        except ClientError as e:
            self.stdout.write(self.style.ERROR(f'   ❌ SES connection failed: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error: {e}'))
        
        # Test 4: Check verified email addresses
        self.stdout.write('\n4. Checking Verified Email Addresses:')
        try:
            ses_client = boto3.client('ses', region_name=getattr(settings, 'AWS_SES_REGION_NAME', 'ap-south-1'))
            response = ses_client.list_verified_email_addresses()
            verified_emails = response.get('VerifiedEmailAddresses', [])
            if verified_emails:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Found {len(verified_emails)} verified email(s):'))
                for email in verified_emails:
                    self.stdout.write(f'      - {email}')
            else:
                self.stdout.write(self.style.WARNING('   ⚠️ No verified email addresses found'))
        except ClientError as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Could not list verified emails: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error: {e}'))
        
        # Test 5: Send test email
        self.stdout.write('\n5. Testing Email Sending:')
        try:
            result = send_mail(
                'AWS SES Test Email',
                'This is a test email to verify AWS SES integration.',
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],  # Send to self for testing
                fail_silently=False,
            )
            if result:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Test email sent successfully'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Failed to send test email'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Email sending failed: {e}'))
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('AWS SES test completed!'))
