from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dermatology.models import DermatologyDepartment, SkinCondition
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Load initial data for dermatology module'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Loading initial dermatology data...'))

        # Create default department
        department, created = DermatologyDepartment.objects.get_or_create(
            name='General Dermatology',
            defaults={
                'description': 'Comprehensive dermatological care including medical, surgical, and cosmetic dermatology',
                'location': 'Medical Center - Wing B, Floor 3',
                'contact_phone': '+1-555-0123',
                'contact_email': 'dermatology@healthcare.com',
                'operating_hours': 'Monday-Friday: 8:00 AM - 5:00 PM',
                'emergency_services': False,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'Created department: {department.name}')

        # Create specialized departments
        departments_data = [
            {
                'name': 'Pediatric Dermatology',
                'description': 'Specialized dermatological care for infants, children, and adolescents',
                'location': 'Pediatric Wing - Floor 2',
                'emergency_services': False
            },
            {
                'name': 'Dermatopathology',
                'description': 'Microscopic examination and diagnosis of skin diseases',
                'location': 'Pathology Lab - Basement Level',
                'emergency_services': False
            },
            {
                'name': 'Cosmetic Dermatology',
                'description': 'Aesthetic treatments and cosmetic procedures',
                'location': 'Cosmetic Center - Floor 4',
                'emergency_services': False
            },
            {
                'name': 'Emergency Dermatology',
                'description': 'Urgent dermatological conditions and emergencies',
                'location': 'Emergency Department',
                'emergency_services': True
            }
        ]

        for dept_data in departments_data:
            dept, created = DermatologyDepartment.objects.get_or_create(
                name=dept_data['name'],
                defaults={
                    'description': dept_data['description'],
                    'location': dept_data['location'],
                    'emergency_services': dept_data['emergency_services'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created department: {dept.name}')

        # Load common skin conditions
        skin_conditions_data = [
            # Inflammatory conditions
            {
                'name': 'Acne Vulgaris',
                'icd10_code': 'L70.0',
                'category': 'inflammatory',
                'severity_level': 'moderate',
                'description': 'Common inflammatory skin condition affecting hair follicles',
                'symptoms': 'Comedones, papules, pustules, nodules, cysts',
                'is_contagious': False,
                'requires_biopsy': False,
                'typical_duration': '2-5 years (adolescent acne)',
                'recurrence_rate': Decimal('60.00')
            },
            {
                'name': 'Atopic Dermatitis (Eczema)',
                'icd10_code': 'L20.9',
                'category': 'inflammatory',
                'severity_level': 'moderate',
                'description': 'Chronic inflammatory skin condition with genetic predisposition',
                'symptoms': 'Dry skin, erythema, scaling, pruritus, lichenification',
                'is_contagious': False,
                'requires_biopsy': False,
                'typical_duration': 'Chronic with flares',
                'recurrence_rate': Decimal('80.00')
            },
            {
                'name': 'Psoriasis',
                'icd10_code': 'L40.9',
                'category': 'autoimmune',
                'severity_level': 'moderate',
                'description': 'Chronic autoimmune skin condition with rapid cell turnover',
                'symptoms': 'Silvery scales, well-demarcated plaques, nail changes',
                'is_contagious': False,
                'requires_biopsy': True,
                'typical_duration': 'Chronic lifelong condition',
                'recurrence_rate': Decimal('90.00')
            },
            {
                'name': 'Seborrheic Dermatitis',
                'icd10_code': 'L21.9',
                'category': 'inflammatory',
                'severity_level': 'mild',
                'description': 'Inflammatory skin condition affecting sebaceous gland areas',
                'symptoms': 'Greasy scales, erythema, pruritus in sebaceous areas',
                'is_contagious': False,
                'requires_biopsy': False,
                'typical_duration': 'Chronic with seasonal variation',
                'recurrence_rate': Decimal('70.00')
            },
            
            # Infectious conditions
            {
                'name': 'Impetigo',
                'icd10_code': 'L01.0',
                'category': 'infectious',
                'severity_level': 'mild',
                'description': 'Superficial bacterial skin infection',
                'symptoms': 'Honey-crusted lesions, vesicles, bullae',
                'is_contagious': True,
                'requires_biopsy': False,
                'typical_duration': '1-2 weeks with treatment',
                'recurrence_rate': Decimal('20.00')
            },
            {
                'name': 'Tinea Corporis (Ringworm)',
                'icd10_code': 'B35.4',
                'category': 'infectious',
                'severity_level': 'mild',
                'description': 'Fungal infection of the body',
                'symptoms': 'Annular scaly patches with central clearing',
                'is_contagious': True,
                'requires_biopsy': False,
                'typical_duration': '2-4 weeks with treatment',
                'recurrence_rate': Decimal('15.00')
            },
            {
                'name': 'Herpes Simplex',
                'icd10_code': 'B00.9',
                'category': 'infectious',
                'severity_level': 'moderate',
                'description': 'Viral infection causing recurrent lesions',
                'symptoms': 'Vesicles, erosions, crusting, burning sensation',
                'is_contagious': True,
                'requires_biopsy': False,
                'typical_duration': '7-10 days per episode',
                'recurrence_rate': Decimal('85.00')
            },

            # Neoplastic conditions
            {
                'name': 'Basal Cell Carcinoma',
                'icd10_code': 'C44.9',
                'category': 'neoplastic',
                'severity_level': 'moderate',
                'description': 'Most common form of skin cancer',
                'symptoms': 'Pearly papule, ulceration, telangiectasia',
                'is_contagious': False,
                'requires_biopsy': True,
                'typical_duration': 'Progressive without treatment',
                'recurrence_rate': Decimal('5.00')
            },
            {
                'name': 'Squamous Cell Carcinoma',
                'icd10_code': 'C44.92',
                'category': 'neoplastic',
                'severity_level': 'severe',
                'description': 'Second most common skin cancer with metastatic potential',
                'symptoms': 'Scaly patch, ulceration, hyperkeratosis',
                'is_contagious': False,
                'requires_biopsy': True,
                'typical_duration': 'Progressive without treatment',
                'recurrence_rate': Decimal('10.00')
            },
            {
                'name': 'Melanoma',
                'icd10_code': 'C43.9',
                'category': 'neoplastic',
                'severity_level': 'critical',
                'description': 'Aggressive skin cancer arising from melanocytes',
                'symptoms': 'Asymmetric, irregular borders, color variation, large diameter',
                'is_contagious': False,
                'requires_biopsy': True,
                'typical_duration': 'Progressive without treatment',
                'recurrence_rate': Decimal('15.00')
            },

            # Allergic conditions
            {
                'name': 'Contact Dermatitis',
                'icd10_code': 'L25.9',
                'category': 'allergic',
                'severity_level': 'moderate',
                'description': 'Inflammatory reaction to contact allergens or irritants',
                'symptoms': 'Erythema, vesicles, scaling, pruritus in contact pattern',
                'is_contagious': False,
                'requires_biopsy': False,
                'typical_duration': '1-3 weeks with avoidance',
                'recurrence_rate': Decimal('50.00')
            },
            {
                'name': 'Urticaria (Hives)',
                'icd10_code': 'L50.9',
                'category': 'allergic',
                'severity_level': 'mild',
                'description': 'Acute or chronic allergic skin reaction',
                'symptoms': 'Wheals, pruritus, angioedema',
                'is_contagious': False,
                'requires_biopsy': False,
                'typical_duration': 'Hours to days (acute), >6 weeks (chronic)',
                'recurrence_rate': Decimal('30.00')
            },

            # Genetic conditions
            {
                'name': 'Ichthyosis Vulgaris',
                'icd10_code': 'Q80.0',
                'category': 'genetic',
                'severity_level': 'moderate',
                'description': 'Genetic disorder of keratinization',
                'symptoms': 'Dry, scaly skin resembling fish scales',
                'is_contagious': False,
                'requires_biopsy': True,
                'typical_duration': 'Lifelong condition',
                'recurrence_rate': Decimal('100.00')
            },

            # Cosmetic conditions
            {
                'name': 'Melasma',
                'icd10_code': 'L81.1',
                'category': 'cosmetic',
                'severity_level': 'mild',
                'description': 'Hyperpigmentation disorder triggered by hormones and sun',
                'symptoms': 'Symmetric brown patches on face',
                'is_contagious': False,
                'requires_biopsy': False,
                'typical_duration': 'Months to years',
                'recurrence_rate': Decimal('75.00')
            },
            {
                'name': 'Age Spots (Solar Lentigines)',
                'icd10_code': 'L81.4',
                'category': 'cosmetic',
                'severity_level': 'mild',
                'description': 'Benign hyperpigmented lesions from sun exposure',
                'symptoms': 'Well-demarcated brown spots on sun-exposed areas',
                'is_contagious': False,
                'requires_biopsy': False,
                'typical_duration': 'Permanent without treatment',
                'recurrence_rate': Decimal('25.00')
            }
        ]

        created_conditions = 0
        for condition_data in skin_conditions_data:
            condition, created = SkinCondition.objects.get_or_create(
                name=condition_data['name'],
                defaults=condition_data
            )
            if created:
                created_conditions += 1
                self.stdout.write(f'Created condition: {condition.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded dermatology data:\n'
                f'- {DermatologyDepartment.objects.count()} departments\n'
                f'- {SkinCondition.objects.count()} skin conditions\n'
                f'- {created_conditions} new conditions created'
            )
        )
