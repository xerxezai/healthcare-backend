#!/bin/bash
# Quick Setup Script for Healthcare Platform Email Notifications
# Uses verified sender: info@xerxez.in

echo "🏥 Healthcare Platform - Email Notification Setup"
echo "📧 Using verified sender: info@xerxez.in"
echo "=============================================="

# Check if we're in the backend directory
if [ ! -f "manage.py" ]; then
    echo "❌ Please run this script from the backend directory (where manage.py is located)"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created from template"
    echo "⚠️  Please edit .env file and add your AWS credentials"
else
    echo "✅ .env file already exists"
fi

# Install required dependencies
echo "📦 Installing required Python packages..."
pip install boto3 botocore python-dotenv

# Test the configuration
echo "🧪 Testing email configuration..."
python test_verified_email.py

echo ""
echo "🚀 NEXT STEPS:"
echo "1. Edit .env file and add your AWS Access Key ID and Secret Access Key"
echo "2. Ensure info@xerxez.in is verified in AWS SES console"
echo "3. Run: python manage.py configure_aws_notifications --interactive"
echo "4. Test email sending: python test_verified_email.py"
echo ""
echo "📚 Documentation: See AWS_NOTIFICATION_GUIDE.md for detailed setup"
