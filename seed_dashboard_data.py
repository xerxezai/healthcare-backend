#!/usr/bin/env python
"""
Seed the database with sample data for realistic dashboard metrics
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from subscriptions.models import (
    SubscriptionPlan, UserSubscription, BillingHistory
)

User = get_user_model()

def create_sample_plans():
    """Create sample subscription plans if they don't exist"""
    plans = [
        {
            'name': 'Basic Medical',
            'description': 'Basic medical management features',
            'price_monthly': Decimal('29.99'),
            'currency': 'USD',
            'is_active': True
        },
        {
            'name': 'Professional Care',
            'description': 'Advanced medical features with analytics',
            'price_monthly': Decimal('79.99'),
            'currency': 'USD',
            'is_active': True
        },
        {
            'name': 'Enterprise Health',
            'description': 'Full featured medical system for hospitals',
            'price_monthly': Decimal('199.99'),
            'currency': 'USD',
            'is_active': True
        }
    ]
    
    created_plans = []
    for plan_data in plans:
        plan, created = SubscriptionPlan.objects.get_or_create(
            name=plan_data['name'],
            defaults=plan_data
        )
        created_plans.append(plan)
        if created:
            print(f"✅ Created plan: {plan.name}")
        else:
            print(f"📋 Plan already exists: {plan.name}")
    
    return created_plans

def create_sample_users():
    """Create sample users if they don't exist"""
    sample_users = [
        {
            'email': 'doctor1@hospital.com',
            'username': 'doctor1@hospital.com',
            'first_name': 'Dr. Sarah',
            'last_name': 'Johnson'
        },
        {
            'email': 'admin@clinic.com',
            'username': 'admin@clinic.com',
            'first_name': 'Admin',
            'last_name': 'Smith'
        },
        {
            'email': 'nurse@medical.com',
            'username': 'nurse@medical.com',
            'first_name': 'Nurse',
            'last_name': 'Williams'
        }
    ]
    
    created_users = []
    for user_data in sample_users:
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults={
                **user_data,
                'is_active': True
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            print(f"✅ Created user: {user.email}")
        else:
            print(f"👤 User already exists: {user.email}")
        created_users.append(user)
    
    return created_users

def create_sample_subscriptions(users, plans):
    """Create sample subscriptions for users"""
    if not plans:
        print("❌ No plans available to create subscriptions")
        return []
    
    subscriptions = []
    today = timezone.now().date()
    
    for i, user in enumerate(users):
        # Skip the first user (might be admin)
        if i == 0:
            continue
            
        plan = random.choice(plans)
        start_date = today - timedelta(days=random.randint(1, 90))
        end_date = start_date + timedelta(days=30)
        
        subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            plan=plan,
            defaults={
                'status': random.choice(['active', 'trial']),
                'start_date': start_date,
                'end_date': end_date,
                'auto_renew': True
            }
        )
        
        if created:
            subscriptions.append(subscription)
            print(f"✅ Created subscription: {user.email} -> {plan.name}")
        else:
            print(f"📋 Subscription already exists: {user.email} -> {plan.name}")
    
    return subscriptions

def create_sample_billing(subscriptions):
    """Create sample billing history"""
    billing_records = []
    
    for subscription in subscriptions:
        # Create 1-3 billing records per subscription
        num_records = random.randint(1, 3)
        
        for i in range(num_records):
            date_paid = timezone.make_aware(
                timezone.datetime.combine(
                    subscription.start_date + timedelta(days=i*30), 
                    timezone.datetime.min.time()
                )
            )
            
            billing, created = BillingHistory.objects.get_or_create(
                user=subscription.user,
                user_subscription=subscription,
                date_paid=date_paid,
                defaults={
                    'amount_due': subscription.plan.price_monthly,
                    'amount_paid': subscription.plan.price_monthly,
                    'currency': subscription.plan.currency.lower(),
                    'status': 'succeeded',
                    'plan_name_snapshot': subscription.plan.name,
                    'payment_gateway_charge_id': f'ch_{random.randint(100000, 999999)}'
                }
            )
            
            if created:
                billing_records.append(billing)
                print(f"✅ Created billing: {subscription.user.email} - ${billing.amount_paid}")
            else:
                print(f"💳 Billing already exists: {subscription.user.email}")
    
    return billing_records

def main():
    print("🌱 Seeding database with sample data for dashboard...")
    print("=" * 50)
    
    # Create sample data
    plans = create_sample_plans()
    print()
    
    users = list(User.objects.all())
    new_users = create_sample_users()
    all_users = users + new_users
    print()
    
    subscriptions = create_sample_subscriptions(all_users, plans)
    print()
    
    billing_records = create_sample_billing(subscriptions)
    print()
    
    # Display summary
    print("=" * 50)
    print("📊 DATABASE SUMMARY")
    print("=" * 50)
    print(f"Total Users: {User.objects.count()}")
    print(f"Total Plans: {SubscriptionPlan.objects.count()}")
    print(f"Total Subscriptions: {UserSubscription.objects.count()}")
    print(f"Active Subscriptions: {UserSubscription.objects.filter(status='active').count()}")
    print(f"Total Billing Records: {BillingHistory.objects.count()}")
    print(f"Total Revenue: ${BillingHistory.objects.filter(status='succeeded').aggregate(total=models.Sum('amount_paid'))['total'] or 0}")
    print()
    print("✅ Database seeding completed!")
    print("🚀 You can now view realistic data in the admin dashboard!")

if __name__ == '__main__':
    main()
