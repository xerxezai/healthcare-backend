#!/usr/bin/env python
"""
Quick AWS SES Test with Verification Check
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

import boto3
from django.conf import settings

def check_aws_ses_setup():
    """Check AWS SES setup and verification status"""
    print("🔍 AWS SES Configuration Check")
    print("="*50)
    
    try:
        # Initialize AWS SES client
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_SES_REGION
        )
        
        print("✅ AWS SES Client initialized successfully")
        print(f"📍 Region: {settings.AWS_SES_REGION}")
        print(f"📧 From Email: {settings.AWS_SES_FROM_EMAIL}")
        
        # Check verified email addresses
        verified_emails = ses_client.list_verified_email_addresses()
        print(f"\n📋 Verified Email Addresses: {len(verified_emails['VerifiedEmailAddresses'])}")
        
        for email in verified_emails['VerifiedEmailAddresses']:
            print(f"  ✅ {email}")
            
        # Check if our from email is verified
        if settings.AWS_SES_FROM_EMAIL in verified_emails['VerifiedEmailAddresses']:
            print(f"\n✅ From email {settings.AWS_SES_FROM_EMAIL} is verified!")
            
            # Try sending a test email to the verified address
            print(f"\n📧 Sending test email to verified address...")
            
            response = ses_client.send_email(
                Source=settings.AWS_SES_FROM_EMAIL,
                Destination={'ToAddresses': [settings.AWS_SES_FROM_EMAIL]},
                Message={
                    'Subject': {'Data': '🧪 AWS SES Admin Notification Test', 'Charset': 'UTF-8'},
                    'Body': {
                        'Html': {
                            'Data': '''
                            <h2>🎉 AWS SES Test Successful!</h2>
                            <p>This confirms that AWS SES is working for admin account notifications.</p>
                            <p><strong>Healthcare Platform</strong> can now send email notifications when admin accounts are created.</p>
                            ''',
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            print(f"✅ Test email sent successfully!")
            print(f"📨 Message ID: {response['MessageId']}")
            return True
            
        else:
            print(f"\n❌ From email {settings.AWS_SES_FROM_EMAIL} is NOT verified")
            print("\n🔧 To fix this:")
            print("1. Go to AWS SES Console")
            print("2. Verify the email address: info@xerxez.in")
            print("3. Check email for verification link")
            
        return False
        
    except Exception as e:
        print(f"❌ AWS SES Error: {e}")
        return False

if __name__ == "__main__":
    success = check_aws_ses_setup()
    
    if success:
        print("\n🎉 AWS SES is fully configured and working!")
        print("✅ Admin account creation emails will now be sent automatically.")
    else:
        print("\n⚠️  AWS SES needs setup. Admin emails won't be sent until fixed.")
        print("\n🔧 Quick Fix Options:")
        print("1. Verify info@xerxez.in in AWS SES Console")
        print("2. Or fix Gmail App Password in .env file")
        print("3. Or use a different verified email service")
