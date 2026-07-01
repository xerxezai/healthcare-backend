#!/usr/bin/env python
import os
import sys
import django
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from subscriptions.models import Service, SubscriptionPlan

def load_subscription_data():
    # Load the JSON data
    with open('load/subscription_plans.json', 'r') as f:
        data = json.load(f)
    
    print("Loading subscription data...")
    
    # Create services first
    services_created = 0
    for item in data:
        if item['model'] == 'subscriptions.service':
            service, created = Service.objects.get_or_create(
                pk=item['pk'],
                defaults=item['fields']
            )
            if created:
                services_created += 1
                print(f"✅ Created service: {service.name}")
            else:
                print(f"⚠️ Service already exists: {service.name}")
    
    # Create subscription plans
    plans_created = 0
    for item in data:
        if item['model'] == 'subscriptions.subscriptionplan':
            fields = item['fields'].copy()
            services = fields.pop('services', [])  # Remove services for now
            
            plan, created = SubscriptionPlan.objects.get_or_create(
                pk=item['pk'],
                defaults=fields
            )
            
            if created or not plan.services.exists():
                # Add services to the plan
                for service_id in services:
                    try:
                        service = Service.objects.get(pk=service_id)
                        plan.services.add(service)
                    except Service.DoesNotExist:
                        print(f"❌ Service with ID {service_id} not found")
                
                if created:
                    plans_created += 1
                    print(f"✅ Created plan: {plan.name}")
                else:
                    print(f"⚠️ Updated plan services: {plan.name}")
            else:
                print(f"⚠️ Plan already exists: {plan.name}")
    
    print(f"\n📊 Summary:")
    print(f"   Services created: {services_created}")
    print(f"   Plans created: {plans_created}")
    print(f"   Total services: {Service.objects.count()}")
    print(f"   Total plans: {SubscriptionPlan.objects.count()}")

if __name__ == '__main__':
    try:
        load_subscription_data()
        print("\n✅ Subscription data loaded successfully!")
    except Exception as e:
        print(f"\n❌ Error loading subscription data: {e}")
        import traceback
        traceback.print_exc()
