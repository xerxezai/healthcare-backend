"""
Django management command to populate default subscription plans and features
"""

from django.core.management.base import BaseCommand
from billing.models import SubscriptionPlan, SubscriptionFeature


class Command(BaseCommand):
    help = 'Create default subscription plans and features'

    def handle(self, *args, **options):
        self.stdout.write('Creating default subscription plans and features...')
        
        # Create default subscription plans
        plans = [
            {
                'plan_type': 'base',
                'plan_name': 'Base Healthcare Platform',
                'description': 'Essential healthcare management features including patient management, basic reporting, user access control, and data backup.',
                'base_monthly_price': 100,
                'included_features': ['patient_management', 'basic_reporting', 'user_access', 'data_backup']
            },
            {
                'plan_type': 'starter',
                'plan_name': 'Starter Practice',
                'description': 'Base platform plus advanced scheduling for small practices.',
                'base_monthly_price': 200,
                'included_features': ['patient_management', 'basic_reporting', 'user_access', 'data_backup', 'appointment_advanced']
            },
            {
                'plan_type': 'professional',
                'plan_name': 'Professional Practice',
                'description': 'Comprehensive solution for growing practices with AI diagnosis and telemedicine.',
                'base_monthly_price': 350,
                'included_features': ['patient_management', 'basic_reporting', 'user_access', 'data_backup', 'appointment_advanced', 'ai_diagnosis', 'telemedicine']
            },
            {
                'plan_type': 'enterprise',
                'plan_name': 'Enterprise Practice',
                'description': 'Complete solution for large practices with all features and priority support.',
                'base_monthly_price': 500,
                'included_features': ['patient_management', 'basic_reporting', 'user_access', 'data_backup', 'appointment_advanced', 'ai_diagnosis', 'telemedicine', 'radiology', 'lab_management', 'analytics']
            }
        ]
        
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                plan_type=plan_data['plan_type'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'✓ Created plan: {plan.plan_name}')
            else:
                self.stdout.write(f'- Plan already exists: {plan.plan_name}')
        
        # Create subscription features
        features = [
            {
                'feature_code': 'ai_diagnosis',
                'feature_name': 'AI Diagnosis Module',
                'description': 'Machine learning diagnostic support and analysis for enhanced patient care.',
                'monthly_price': 100,
                'icon': '🤖'
            },
            {
                'feature_code': 'radiology',
                'feature_name': 'Radiology Services',
                'description': 'Medical imaging management and analysis tools for comprehensive diagnostics.',
                'monthly_price': 100,
                'icon': '🔬'
            },
            {
                'feature_code': 'lab_management',
                'feature_name': 'Laboratory Management',
                'description': 'Complete lab test management and reporting system.',
                'monthly_price': 100,
                'icon': '🧪'
            },
            {
                'feature_code': 'telemedicine',
                'feature_name': 'Telemedicine Suite',
                'description': 'Virtual consultations and remote patient monitoring capabilities.',
                'monthly_price': 100,
                'icon': '💻'
            },
            {
                'feature_code': 'appointment_advanced',
                'feature_name': 'Advanced Scheduling',
                'description': 'Advanced appointment scheduling with automated reminders and calendar integration.',
                'monthly_price': 100,
                'icon': '📅'
            },
            {
                'feature_code': 'analytics',
                'feature_name': 'Advanced Analytics',
                'description': 'Detailed reporting and business intelligence dashboards for practice insights.',
                'monthly_price': 100,
                'icon': '📊'
            },
            {
                'feature_code': 'pathology',
                'feature_name': 'Pathology Management',
                'description': 'Comprehensive pathology workflow and specimen tracking system.',
                'monthly_price': 100,
                'icon': '🔬'
            },
            {
                'feature_code': 'billing_advanced',
                'feature_name': 'Advanced Billing',
                'description': 'Enhanced billing features with insurance claim processing and payment tracking.',
                'monthly_price': 100,
                'icon': '💳'
            },
            {
                'feature_code': 'reporting',
                'feature_name': 'Custom Reporting',
                'description': 'Generate custom reports and export data for analysis and compliance.',
                'monthly_price': 100,
                'icon': '📋'
            },
            {
                'feature_code': 'integration',
                'feature_name': 'Third-party Integrations',
                'description': 'Connect with external systems, EMRs, and healthcare APIs.',
                'monthly_price': 100,
                'icon': '🔗'
            }
        ]
        
        for feature_data in features:
            feature, created = SubscriptionFeature.objects.get_or_create(
                feature_code=feature_data['feature_code'],
                defaults=feature_data
            )
            if created:
                self.stdout.write(f'✓ Created feature: {feature.feature_name}')
            else:
                self.stdout.write(f'- Feature already exists: {feature.feature_name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully created default subscription plans and features!'))
