from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pathology.models import PathologyDepartment, PathologyTest
import json


class Command(BaseCommand):
    help = 'Load sample pathology data for testing and development'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample pathology data...')
        
        # Create sample pathology department
        department, created = PathologyDepartment.objects.get_or_create(
            code='MAIN',
            defaults={
                'name': 'Main Pathology Laboratory',
                'location': 'Medical Center Building A, Floor 3',
                'phone': '+1-555-0123',
                'email': 'pathology@hospital.com',
                'accreditation_number': 'CAP-2024-001'
            }
        )
        
        if created:
            self.stdout.write(f'Created department: {department.name}')
        
        # Sample pathology tests
        sample_tests = [
            # Histopathology
            {
                'name': 'Tissue Biopsy - Routine',
                'code': 'HISTO-001',
                'category': 'histopathology',
                'description': 'Routine histopathological examination of tissue specimen',
                'specimen_type': 'Tissue',
                'normal_range': 'No malignant cells detected',
                'test_methodology': 'H&E staining with microscopic examination',
                'processing_time_hours': 24,
                'cost': 150.00
            },
            {
                'name': 'Frozen Section',
                'code': 'HISTO-002',
                'category': 'histopathology',
                'description': 'Rapid intraoperative histopathological diagnosis',
                'specimen_type': 'Tissue',
                'normal_range': 'No malignant cells detected',
                'test_methodology': 'Frozen section with H&E staining',
                'processing_time_hours': 1,
                'cost': 200.00
            },
            
            # Cytopathology
            {
                'name': 'Pap Smear',
                'code': 'CYTO-001',
                'category': 'cytopathology',
                'description': 'Cervical cytology screening',
                'specimen_type': 'Cervical cells',
                'normal_range': 'NILM (Negative for intraepithelial lesion)',
                'test_methodology': 'Liquid-based cytology',
                'processing_time_hours': 8,
                'cost': 75.00
            },
            {
                'name': 'Fine Needle Aspiration (FNA)',
                'code': 'CYTO-002',
                'category': 'cytopathology',
                'description': 'Cytological examination of FNA specimen',
                'specimen_type': 'Aspirated cells',
                'normal_range': 'Benign cellular elements',
                'test_methodology': 'Diff-Quik and Papanicolaou staining',
                'processing_time_hours': 4,
                'cost': 120.00
            },
            
            # Hematology
            {
                'name': 'Complete Blood Count (CBC)',
                'code': 'HEMA-001',
                'category': 'hematology',
                'description': 'Complete blood count with differential',
                'specimen_type': 'Whole blood (EDTA)',
                'normal_range': 'WBC: 4.5-11.0 x10³/µL, RBC: 4.5-5.5 x10⁶/µL, Hgb: 12-16 g/dL',
                'test_methodology': 'Automated cell counter with manual differential',
                'processing_time_hours': 2,
                'cost': 25.00
            },
            {
                'name': 'Bone Marrow Biopsy',
                'code': 'HEMA-002',
                'category': 'hematology',
                'description': 'Bone marrow histopathology and cytology',
                'specimen_type': 'Bone marrow',
                'normal_range': 'Normal cellular morphology and distribution',
                'test_methodology': 'H&E staining with special stains as needed',
                'processing_time_hours': 48,
                'cost': 300.00
            },
            
            # Clinical Chemistry
            {
                'name': 'Comprehensive Metabolic Panel',
                'code': 'CHEM-001',
                'category': 'clinical_chemistry',
                'description': 'Basic metabolic panel with liver function tests',
                'specimen_type': 'Serum',
                'normal_range': 'Glucose: 70-100 mg/dL, Creatinine: 0.6-1.2 mg/dL',
                'test_methodology': 'Automated chemistry analyzer',
                'processing_time_hours': 2,
                'cost': 45.00
            },
            {
                'name': 'Cardiac Markers',
                'code': 'CHEM-002',
                'category': 'clinical_chemistry',
                'description': 'Troponin I, CK-MB, Myoglobin',
                'specimen_type': 'Serum',
                'normal_range': 'Troponin I: <0.04 ng/mL',
                'test_methodology': 'Immunoassay',
                'processing_time_hours': 1,
                'cost': 85.00
            },
            
            # Microbiology
            {
                'name': 'Bacterial Culture',
                'code': 'MICRO-001',
                'category': 'microbiology',
                'description': 'Bacterial culture with antibiotic sensitivity',
                'specimen_type': 'Various clinical specimens',
                'normal_range': 'No pathogenic bacteria isolated',
                'test_methodology': 'Culture on selective media with sensitivity testing',
                'processing_time_hours': 48,
                'cost': 60.00
            },
            {
                'name': 'Fungal Culture',
                'code': 'MICRO-002',
                'category': 'microbiology',
                'description': 'Fungal culture and identification',
                'specimen_type': 'Various clinical specimens',
                'normal_range': 'No pathogenic fungi isolated',
                'test_methodology': 'Culture on Sabouraud dextrose agar',
                'processing_time_hours': 168,  # 7 days
                'cost': 80.00
            },
            
            # Immunology
            {
                'name': 'Autoimmune Panel',
                'code': 'IMMUNO-001',
                'category': 'immunology',
                'description': 'ANA, Anti-dsDNA, Anti-Sm, Anti-SSA/SSB',
                'specimen_type': 'Serum',
                'normal_range': 'Negative or low titer',
                'test_methodology': 'Immunofluorescence and ELISA',
                'processing_time_hours': 24,
                'cost': 150.00
            },
            
            # Molecular Pathology
            {
                'name': 'PCR for Infectious Agents',
                'code': 'MOLEC-001',
                'category': 'molecular',
                'description': 'Real-time PCR for pathogen detection',
                'specimen_type': 'Various clinical specimens',
                'normal_range': 'Not detected',
                'test_methodology': 'Real-time PCR',
                'processing_time_hours': 8,
                'cost': 180.00
            },
            
            # Genetic Testing
            {
                'name': 'BRCA1/BRCA2 Mutation Analysis',
                'code': 'GENET-001',
                'category': 'genetic',
                'description': 'Genetic testing for BRCA1 and BRCA2 mutations',
                'specimen_type': 'Whole blood or tissue',
                'normal_range': 'No pathogenic variants detected',
                'test_methodology': 'Next-generation sequencing',
                'processing_time_hours': 168,  # 7 days
                'cost': 500.00
            }
        ]
        
        # Create sample tests
        tests_created = 0
        for test_data in sample_tests:
            test, created = PathologyTest.objects.get_or_create(
                code=test_data['code'],
                defaults=test_data
            )
            
            if created:
                tests_created += 1
                self.stdout.write(f'Created test: {test.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded pathology data:\n'
                f'- Departments: 1\n'
                f'- Tests: {tests_created} new tests created'
            )
        )
