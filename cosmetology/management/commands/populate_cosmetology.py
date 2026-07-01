from django.core.management.base import BaseCommand
from cosmetology.models import CosmetologyService, CosmetologyProduct

class Command(BaseCommand):
    help = 'Populate the database with sample cosmetology services and products'

    def handle(self, *args, **options):
        # Sample Services Data
        services_data = [
            # Facial Treatments
            {
                'name': 'HydraFacial MD',
                'category': 'facial',
                'description': 'Multi-step facial treatment that cleanses, exfoliates, extracts, and hydrates skin using patented technology.',
                'duration': 45,
                'price': 150.00,
                'requirements': ['Skin consultation', 'Remove makeup'],
                'contraindications': ['Active acne inflammation', 'Recent chemical peels'],
                'aftercare_instructions': 'Avoid sun exposure for 24 hours. Use gentle cleanser and moisturizer.',
                'requires_consultation': False,
                'session_gap_days': 14
            },
            {
                'name': 'Chemical Peel - Glycolic',
                'category': 'facial',
                'description': 'Alpha hydroxy acid peel to improve skin texture, reduce fine lines, and brighten complexion.',
                'duration': 30,
                'price': 120.00,
                'requirements': ['Patch test 48hrs prior', 'No retinol use 1 week before'],
                'contraindications': ['Pregnancy', 'Active infections', 'Recent sun exposure'],
                'aftercare_instructions': 'Gentle cleansing only. SPF mandatory. Expect peeling for 3-5 days.',
                'requires_consultation': True,
                'session_gap_days': 21
            },
            {
                'name': 'Anti-Aging Facial',
                'category': 'facial',
                'description': 'Comprehensive facial targeting fine lines, wrinkles, and age spots with advanced serums and techniques.',
                'duration': 75,
                'price': 180.00,
                'requirements': ['Skin analysis', 'Allergy assessment'],
                'contraindications': ['Severe rosacea', 'Open wounds'],
                'aftercare_instructions': 'Use provided home care products. Schedule follow-up in 4 weeks.',
                'requires_consultation': False,
                'session_gap_days': 28
            },

            # Hair Services
            {
                'name': 'Keratin Hair Treatment',
                'category': 'hair',
                'description': 'Professional smoothing treatment that reduces frizz and adds shine for up to 4 months.',
                'duration': 180,
                'price': 300.00,
                'requirements': ['Hair wash before arrival', 'No chemical processing 2 weeks prior'],
                'contraindications': ['Heavily damaged hair', 'Recent bleaching'],
                'aftercare_instructions': 'No washing for 72 hours. Use sulfate-free shampoo only.',
                'requires_consultation': True,
                'session_gap_days': 120
            },
            {
                'name': 'Hair Botox Treatment',
                'category': 'hair',
                'description': 'Deep conditioning treatment with hyaluronic acid to repair and strengthen damaged hair.',
                'duration': 120,
                'price': 200.00,
                'requirements': ['Clean hair', 'Strand test'],
                'contraindications': ['Scalp irritation', 'Recent color treatment'],
                'aftercare_instructions': 'Use recommended hair masks weekly. Avoid heat styling for 48 hours.',
                'requires_consultation': False,
                'session_gap_days': 60
            },
            {
                'name': 'Professional Hair Cut & Style',
                'category': 'hair',
                'description': 'Expert hair cutting with personalized styling to enhance your natural features.',
                'duration': 60,
                'price': 85.00,
                'requirements': ['Hair consultation', 'Style preference discussion'],
                'contraindications': ['Scalp conditions requiring medical attention'],
                'aftercare_instructions': 'Style as demonstrated. Schedule trim in 6-8 weeks.',
                'requires_consultation': False,
                'session_gap_days': 42
            },

            # Laser Treatments
            {
                'name': 'Laser Hair Removal - Full Legs',
                'category': 'laser',
                'description': 'IPL laser hair removal for permanent hair reduction on full legs.',
                'duration': 45,
                'price': 250.00,
                'requirements': ['Shave 24hrs before', 'No sun exposure 4 weeks'],
                'contraindications': ['Pregnancy', 'Dark tan', 'Recent sun exposure'],
                'aftercare_instructions': 'Apply aloe vera gel. Avoid hot showers for 24 hours. No sun exposure.',
                'requires_consultation': True,
                'session_gap_days': 42
            },
            {
                'name': 'Laser Skin Resurfacing',
                'category': 'laser',
                'description': 'Fractional laser treatment to improve skin texture, reduce scars, and minimize pores.',
                'duration': 60,
                'price': 400.00,
                'requirements': ['Topical anesthetic', 'Pre-treatment skin prep'],
                'contraindications': ['Active acne', 'Keloid scarring tendency'],
                'aftercare_instructions': 'Gentle cleansing only. Apply prescribed ointment. Expect 5-7 days downtime.',
                'requires_consultation': True,
                'session_gap_days': 60
            },

            # Injectable Treatments
            {
                'name': 'Botox - Forehead & Frown Lines',
                'category': 'injectable',
                'description': 'Botulinum toxin injections to reduce dynamic wrinkles in forehead and glabella area.',
                'duration': 30,
                'price': 350.00,
                'requirements': ['Medical consultation', 'No blood thinners 1 week prior'],
                'contraindications': ['Pregnancy', 'Neurological disorders', 'Infection at injection site'],
                'aftercare_instructions': 'No lying down for 4 hours. Avoid exercise for 24 hours. Results in 7-14 days.',
                'requires_consultation': True,
                'session_gap_days': 90
            },
            {
                'name': 'Dermal Fillers - Lip Enhancement',
                'category': 'injectable',
                'description': 'Hyaluronic acid fillers to enhance lip volume and define lip contours.',
                'duration': 45,
                'price': 450.00,
                'requirements': ['Numbing cream', 'Cold therapy preparation'],
                'contraindications': ['Active cold sores', 'Autoimmune conditions'],
                'aftercare_instructions': 'Apply ice as needed. Avoid hot drinks for 24 hours. Gentle lip care.',
                'requires_consultation': True,
                'session_gap_days': 180
            },

            # Nail Services
            {
                'name': 'Luxury Manicure & Gel Polish',
                'category': 'nails',
                'description': 'Complete manicure service with cuticle care, shaping, and long-lasting gel polish application.',
                'duration': 60,
                'price': 55.00,
                'requirements': ['Clean hands', 'Remove existing polish'],
                'contraindications': ['Nail infections', 'Open wounds on hands'],
                'aftercare_instructions': 'Wear gloves for household tasks. Apply cuticle oil daily.',
                'requires_consultation': False,
                'session_gap_days': 21
            },
            {
                'name': 'Spa Pedicure with Shellac',
                'category': 'nails',
                'description': 'Relaxing pedicure with foot soak, exfoliation, callus removal, and durable Shellac polish.',
                'duration': 75,
                'price': 65.00,
                'requirements': ['Clean feet', 'No recent foot injuries'],
                'contraindications': ['Diabetic foot complications', 'Infections'],
                'aftercare_instructions': 'Keep feet dry for 2 hours. Moisturize daily.',
                'requires_consultation': False,
                'session_gap_days': 28
            },

            # Makeup Services
            {
                'name': 'Bridal Makeup Trial',
                'category': 'makeup',
                'description': 'Complete bridal makeup trial with photo documentation and touch-up kit.',
                'duration': 90,
                'price': 120.00,
                'requirements': ['Clean face', 'Bring inspiration photos'],
                'contraindications': ['Severe skin allergies', 'Active skin conditions'],
                'aftercare_instructions': 'Take photos in different lighting. Schedule wedding day 2 weeks in advance.',
                'requires_consultation': True,
                'session_gap_days': 1
            },
            {
                'name': 'Special Event Makeup',
                'category': 'makeup',
                'description': 'Professional makeup application for special occasions with premium products.',
                'duration': 60,
                'price': 85.00,
                'requirements': ['Skincare prep', 'Event details discussion'],
                'contraindications': ['Recent facial treatments', 'Eye infections'],
                'aftercare_instructions': 'Touch-up products provided. Remove gently with cleansing oil.',
                'requires_consultation': False,
                'session_gap_days': 1
            },

            # Body Treatments
            {
                'name': 'Full Body Exfoliation & Moisturizing',
                'category': 'body',
                'description': 'Complete body exfoliation with natural scrubs followed by hydrating body treatment.',
                'duration': 90,
                'price': 140.00,
                'requirements': ['Shower before treatment', 'Loose clothing'],
                'contraindications': ['Sensitive skin conditions', 'Recent sunburn'],
                'aftercare_instructions': 'Avoid hot showers for 24 hours. Apply provided body oil daily.',
                'requires_consultation': False,
                'session_gap_days': 14
            },

            # Wellness & Spa
            {
                'name': 'Aromatherapy Facial Massage',
                'category': 'wellness',
                'description': 'Relaxing facial massage with essential oils to promote circulation and relaxation.',
                'duration': 50,
                'price': 95.00,
                'requirements': ['Essential oil preference discussion', 'Allergy check'],
                'contraindications': ['Severe allergies', 'Recent facial surgery'],
                'aftercare_instructions': 'Stay hydrated. Avoid heavy makeup for 2 hours.',
                'requires_consultation': False,
                'session_gap_days': 7
            }
        ]

        # Sample Products Data
        products_data = [
            # Skincare Products
            {
                'name': 'Vitamin C Brightening Serum',
                'brand': 'SkinMedica',
                'product_type': 'skincare',
                'description': 'Potent antioxidant serum with 20% L-Ascorbic Acid to brighten and protect skin.',
                'ingredients': ['L-Ascorbic Acid', 'Vitamin E', 'Hyaluronic Acid', 'Ferulic Acid'],
                'benefits': ['Brightens skin tone', 'Reduces dark spots', 'Antioxidant protection', 'Improves texture'],
                'skin_types': ['normal', 'oily', 'combination'],
                'usage_instructions': 'Apply 2-3 drops to clean skin in morning. Follow with SPF.',
                'stock_quantity': 25,
                'price': 89.00,
                'cost_price': 45.00,
                'safety_warnings': 'May cause initial sensitivity. Discontinue if irritation persists.'
            },
            {
                'name': 'Retinol Renewal Complex',
                'brand': 'Obagi',
                'product_type': 'skincare',
                'description': 'Advanced retinol formula with 0.5% retinol for anti-aging and skin renewal.',
                'ingredients': ['Retinol 0.5%', 'Peptides', 'Hyaluronic Acid', 'Niacinamide'],
                'benefits': ['Reduces fine lines', 'Improves skin texture', 'Stimulates collagen', 'Evening skin tone'],
                'skin_types': ['normal', 'mature', 'combination'],
                'usage_instructions': 'Start 2x weekly in evening. Gradually increase frequency. Always use SPF.',
                'stock_quantity': 18,
                'price': 125.00,
                'cost_price': 62.50,
                'safety_warnings': 'Not for use during pregnancy. May increase sun sensitivity.'
            },
            {
                'name': 'Hydrating Facial Cleanser',
                'brand': 'CeraVe',
                'product_type': 'skincare',
                'description': 'Gentle, non-foaming cleanser with ceramides and hyaluronic acid for all skin types.',
                'ingredients': ['Ceramides', 'Hyaluronic Acid', 'MVE Technology', 'Niacinamide'],
                'benefits': ['Gentle cleansing', 'Maintains skin barrier', 'Hydrates while cleansing', 'Non-comedogenic'],
                'skin_types': ['dry', 'sensitive', 'normal', 'combination'],
                'usage_instructions': 'Apply to damp skin, massage gently, rinse with lukewarm water.',
                'stock_quantity': 35,
                'price': 32.00,
                'cost_price': 16.00,
                'safety_warnings': 'For external use only. Avoid contact with eyes.'
            },

            # Hair Care Products
            {
                'name': 'Keratin Smoothing Shampoo',
                'brand': 'Brazilian Blowout',
                'product_type': 'haircare',
                'description': 'Sulfate-free shampoo designed to extend the life of keratin treatments.',
                'ingredients': ['Keratin', 'Argan Oil', 'Coconut Oil', 'Panthenol'],
                'benefits': ['Maintains smoothness', 'Reduces frizz', 'Adds shine', 'Sulfate-free'],
                'skin_types': ['chemically treated', 'frizzy', 'damaged'],
                'usage_instructions': 'Apply to wet hair, lather gently, rinse thoroughly. Follow with conditioner.',
                'stock_quantity': 20,
                'price': 45.00,
                'cost_price': 22.50,
                'safety_warnings': 'For chemically treated hair. Avoid contact with eyes.'
            },
            {
                'name': 'Intensive Hair Repair Mask',
                'brand': 'Olaplex',
                'product_type': 'haircare',
                'description': 'Professional-grade hair mask with patented bond-building technology.',
                'ingredients': ['Bis-Aminopropyl Diglycol Dimaleate', 'Shea Butter', 'Protein Complex'],
                'benefits': ['Repairs damaged bonds', 'Strengthens hair', 'Reduces breakage', 'Improves elasticity'],
                'skin_types': ['damaged', 'color_treated', 'chemically processed'],
                'usage_instructions': 'Apply to towel-dried hair, leave for 10 minutes, rinse thoroughly.',
                'stock_quantity': 15,
                'price': 58.00,
                'cost_price': 29.00,
                'safety_warnings': 'For damaged hair only. Conduct strand test before first use.'
            },

            # Makeup Products
            {
                'name': 'HD Foundation',
                'brand': 'Make Up For Ever',
                'product_type': 'makeup',
                'description': 'High-definition liquid foundation with buildable coverage and long-lasting wear.',
                'ingredients': ['Silicones', 'Titanium Dioxide', 'Iron Oxides', 'SPF 15'],
                'benefits': ['HD finish', 'Long-lasting', 'Buildable coverage', 'SPF protection'],
                'skin_types': ['all skin types'],
                'usage_instructions': 'Apply with brush or sponge. Build coverage as needed.',
                'stock_quantity': 30,
                'price': 48.00,
                'cost_price': 24.00,
                'safety_warnings': 'Patch test recommended. Remove thoroughly before bed.'
            },
            {
                'name': 'Waterproof Mascara',
                'brand': 'Urban Decay',
                'product_type': 'makeup',
                'description': 'Volumizing and lengthening waterproof mascara for dramatic lashes.',
                'ingredients': ['Beeswax', 'Carnauba Wax', 'Polymers', 'Pigments'],
                'benefits': ['Waterproof formula', 'Volume and length', 'Long-wearing', 'Smudge-proof'],
                'skin_types': ['all skin types'],
                'usage_instructions': 'Apply from base to tip of lashes. Layer for more drama.',
                'stock_quantity': 40,
                'price': 26.00,
                'cost_price': 13.00,
                'safety_warnings': 'Remove with waterproof makeup remover. Replace every 3 months.'
            },

            # Professional Tools
            {
                'name': 'Professional Steamer',
                'brand': 'Vapozon',
                'product_type': 'tools',
                'description': 'Professional facial steamer for deep pore cleansing and preparation.',
                'ingredients': ['Stainless steel', 'Electronic components'],
                'benefits': ['Opens pores', 'Softens skin', 'Improves product penetration', 'Professional results'],
                'skin_types': ['professional use only'],
                'usage_instructions': 'Use distilled water only. 10-15 minute sessions. Professional use.',
                'stock_quantity': 2,
                'price': 450.00,
                'cost_price': 225.00,
                'safety_warnings': 'Professional use only. Hot steam - maintain safe distance.'
            },

            # Beauty Supplements
            {
                'name': 'Hair Growth Vitamins',
                'brand': 'Viviscal',
                'product_type': 'supplements',
                'description': 'Scientifically formulated supplement to promote healthy hair growth.',
                'ingredients': ['Biotin', 'Marine Collagen', 'Vitamin C', 'Iron', 'Zinc'],
                'benefits': ['Promotes hair growth', 'Strengthens hair', 'Improves hair thickness', 'Clinical proven'],
                'skin_types': ['all hair types'],
                'usage_instructions': 'Take 2 tablets daily with food for minimum 3-6 months.',
                'stock_quantity': 50,
                'price': 39.99,
                'cost_price': 20.00,
                'safety_warnings': 'Consult doctor if pregnant or nursing. Not for children under 18.'
            }
        ]

        # Create Services
        created_services = 0
        for service_data in services_data:
            service, created = CosmetologyService.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            if created:
                created_services += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created service: {service.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Service already exists: {service.name}')
                )

        # Create Products
        created_products = 0
        for product_data in products_data:
            product, created = CosmetologyProduct.objects.get_or_create(
                name=product_data['name'],
                brand=product_data['brand'],
                defaults=product_data
            )
            if created:
                created_products += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created product: {product.brand} - {product.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Product already exists: {product.brand} - {product.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(services_data)} services and {len(products_data)} products. '
                f'Created {created_services} new services and {created_products} new products.'
            )
        )
