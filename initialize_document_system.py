"""
Initialize default registration document types with soft-coded configuration
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from hospital.registration_document_models import (
    RegistrationDocumentType, 
    RegistrationDocumentTemplate
)

def create_default_document_types():
    """Create default document types with soft-coded configuration"""
    
    # Soft-coded document type definitions
    DOCUMENT_TYPES_CONFIG = [
        {
            'name': 'Government-issued Photo ID',
            'description': 'Valid passport, driver\'s license, or national ID card',
            'category': 'identity',
            'is_required': True,
            'priority_level': 'critical',
            'file_size_limit_mb': 5,
            'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
            'display_order': 1,
            'help_text': 'Upload a clear photo of your government-issued ID. Ensure all text is readable.',
            'validation_rules': {
                'min_resolution': '300dpi',
                'require_photo': True,
                'check_expiry': True
            }
        },
        {
            'name': 'Medical License Certificate',
            'description': 'Current medical license issued by recognized medical authority',
            'category': 'license',
            'is_required': True,
            'priority_level': 'critical',
            'file_size_limit_mb': 10,
            'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
            'display_order': 2,
            'help_text': 'Upload your current medical license. License must be valid and not expired.',
            'validation_rules': {
                'check_authority': True,
                'verify_license_number': True,
                'check_expiry': True
            }
        },
        {
            'name': 'Medical Degree Certificate',
            'description': 'University degree in medicine (MBBS, MD, DO, etc.)',
            'category': 'education',
            'is_required': True,
            'priority_level': 'critical',
            'file_size_limit_mb': 10,
            'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
            'display_order': 3,
            'help_text': 'Upload your medical degree certificate from an accredited institution.',
            'validation_rules': {
                'verify_institution': True,
                'check_degree_type': True
            }
        },
        {
            'name': 'Specialization Certificate',
            'description': 'Board certification or specialization training certificate',
            'category': 'education',
            'is_required': False,
            'priority_level': 'high',
            'file_size_limit_mb': 10,
            'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
            'display_order': 4,
            'help_text': 'Upload certificates for any medical specializations (Cardiology, Neurology, etc.)',
            'validation_rules': {
                'verify_board': True,
                'check_specialization_match': True
            }
        },
        {
            'name': 'Professional References',
            'description': 'Letters of recommendation from colleagues or supervisors',
            'category': 'experience',
            'is_required': False,
            'priority_level': 'medium',
            'file_size_limit_mb': 5,
            'allowed_extensions': ['.pdf', '.doc', '.docx'],
            'display_order': 5,
            'help_text': 'Upload 2-3 professional reference letters from medical colleagues or supervisors.',
            'validation_rules': {
                'min_references': 2,
                'verify_contact_info': True
            }
        },
        {
            'name': 'Malpractice Insurance',
            'description': 'Current professional liability insurance certificate',
            'category': 'insurance',
            'is_required': False,
            'priority_level': 'high',
            'file_size_limit_mb': 5,
            'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
            'display_order': 6,
            'help_text': 'Upload your current malpractice insurance certificate (if applicable).',
            'validation_rules': {
                'check_coverage_amount': True,
                'verify_provider': True,
                'check_expiry': True
            }
        },
        {
            'name': 'CV/Resume',
            'description': 'Current curriculum vitae or professional resume',
            'category': 'experience',
            'is_required': True,
            'priority_level': 'medium',
            'file_size_limit_mb': 5,
            'allowed_extensions': ['.pdf', '.doc', '.docx'],
            'display_order': 7,
            'help_text': 'Upload your current CV highlighting medical education and experience.',
            'validation_rules': {
                'check_completeness': True,
                'verify_experience': True
            }
        },
        {
            'name': 'Hospital Affiliation Letter',
            'description': 'Letter from current or previous hospital/clinic employment',
            'category': 'experience',
            'is_required': False,
            'priority_level': 'medium',
            'file_size_limit_mb': 5,
            'allowed_extensions': ['.pdf', '.doc', '.docx'],
            'display_order': 8,
            'help_text': 'Upload employment verification letter from hospital or clinic.',
            'validation_rules': {
                'verify_institution': True,
                'check_contact_info': True
            }
        }
    ]
    
    print("🏥 Creating Registration Document Types with Soft Coding...")
    print("=" * 60)
    
    created_count = 0
    updated_count = 0
    
    for doc_config in DOCUMENT_TYPES_CONFIG:
        doc_type, created = RegistrationDocumentType.objects.get_or_create(
            name=doc_config['name'],
            category=doc_config['category'],
            defaults={
                'description': doc_config['description'],
                'is_required': doc_config['is_required'],
                'priority_level': doc_config['priority_level'],
                'file_size_limit_mb': doc_config['file_size_limit_mb'],
                'allowed_extensions': doc_config['allowed_extensions'],
                'display_order': doc_config['display_order'],
                'help_text': doc_config['help_text'],
                'validation_rules': doc_config['validation_rules']
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ Created: {doc_type.name} ({doc_type.category})")
        else:
            # Update existing with new configuration
            doc_type.description = doc_config['description']
            doc_type.is_required = doc_config['is_required']
            doc_type.priority_level = doc_config['priority_level']
            doc_type.file_size_limit_mb = doc_config['file_size_limit_mb']
            doc_type.allowed_extensions = doc_config['allowed_extensions']
            doc_type.display_order = doc_config['display_order']
            doc_type.help_text = doc_config['help_text']
            doc_type.validation_rules = doc_config['validation_rules']
            doc_type.save()
            updated_count += 1
            print(f"🔄 Updated: {doc_type.name} ({doc_type.category})")
    
    print("\n" + "=" * 60)
    print(f"📊 Summary: {created_count} created, {updated_count} updated")
    return created_count, updated_count

def create_default_templates():
    """Create default document templates for different roles"""
    
    TEMPLATE_CONFIG = {
        'general_doctor': {
            'name': 'General Medical Practitioner Template',
            'description': 'Standard document requirements for general practitioners',
            'region': 'general',
            'requirements': {
                'minimum_documents': 4,
                'required_categories': ['identity', 'license', 'education'],
                'experience_years_minimum': 0
            },
            'validation_rules': {
                'strict_license_validation': True,
                'require_degree_verification': True,
                'allow_new_graduates': True
            }
        },
        'specialist': {
            'name': 'Medical Specialist Template',
            'description': 'Enhanced requirements for medical specialists',
            'region': 'general',
            'requirements': {
                'minimum_documents': 6,
                'required_categories': ['identity', 'license', 'education', 'certification'],
                'experience_years_minimum': 3
            },
            'validation_rules': {
                'strict_license_validation': True,
                'require_degree_verification': True,
                'require_specialization_cert': True,
                'verify_board_certification': True
            }
        }
    }
    
    print("\n🎯 Creating Document Templates...")
    print("-" * 40)
    
    created_templates = 0
    
    for role, config in TEMPLATE_CONFIG.items():
        template, created = RegistrationDocumentTemplate.objects.get_or_create(
            name=config['name'],
            role=role,
            region=config['region'],
            defaults={
                'description': config['description'],
                'requirements': config['requirements'],
                'validation_rules': config['validation_rules']
            }
        )
        
        if created:
            # Add document types to template
            required_categories = config['requirements']['required_categories']
            doc_types = RegistrationDocumentType.objects.filter(
                category__in=required_categories,
                is_active=True
            )
            template.document_types.set(doc_types)
            created_templates += 1
            print(f"✅ Created template: {template.name}")
        else:
            print(f"🔄 Template exists: {template.name}")
    
    print(f"📋 Created {created_templates} templates")
    return created_templates

def main():
    """Main function to initialize document system"""
    print("🚀 Initializing Registration Document System")
    print("=" * 70)
    
    try:
        # Create document types
        doc_created, doc_updated = create_default_document_types()
        
        # Create templates
        template_created = create_default_templates()
        
        print("\n🎉 Document System Initialization Complete!")
        print(f"📄 Document Types: {doc_created} created, {doc_updated} updated")
        print(f"📋 Templates: {template_created} created")
        
        print("\n📖 Usage Instructions:")
        print("1. Document types are now available for registration forms")
        print("2. Soft-coded configuration allows easy customization")
        print("3. Templates provide role-based document requirements")
        print("4. All settings can be modified through admin panel or code")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing document system: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
