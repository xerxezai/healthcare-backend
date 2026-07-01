# Healthcare Platform - Email Notification Setup (Windows)
# Uses verified sender: info@xerxez.in

Write-Host "🏥 Healthcare Platform - Email Notification Setup" -ForegroundColor Green
Write-Host "📧 Using verified sender: info@xerxez.in" -ForegroundColor Yellow
Write-Host "=============================================="

# Check if we're in the backend directory
if (!(Test-Path "manage.py")) {
    Write-Host "❌ Please run this script from the backend directory (where manage.py is located)" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Blue
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env file created from template" -ForegroundColor Green
    Write-Host "⚠️  Please edit .env file and add your AWS credentials" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

# Install required dependencies
Write-Host "📦 Installing required Python packages..." -ForegroundColor Blue
pip install boto3 botocore python-dotenv

# Test the configuration
Write-Host "🧪 Testing email configuration..." -ForegroundColor Blue
python test_verified_email.py

Write-Host ""
Write-Host "🚀 NEXT STEPS:" -ForegroundColor Green
Write-Host "1. Edit .env file and add your AWS Access Key ID and Secret Access Key"
Write-Host "2. Ensure info@xerxez.in is verified in AWS SES console"
Write-Host "3. Run: python manage.py configure_aws_notifications --interactive"
Write-Host "4. Test email sending: python test_verified_email.py"
Write-Host ""
Write-Host "📚 Documentation: See AWS_NOTIFICATION_GUIDE.md for detailed setup" -ForegroundColor Cyan
