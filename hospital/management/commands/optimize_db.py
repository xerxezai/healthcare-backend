"""
Django management command to optimize database performance
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction
import time


class Command(BaseCommand):
    """Django command to optimize database performance."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply-indexes',
            action='store_true',
            help='Apply missing indexes to improve performance',
        )
        parser.add_argument(
            '--analyze-vacuum',
            action='store_true',
            help='Run ANALYZE and VACUUM on database',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all optimizations',
        )

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write(self.style.SUCCESS('🚀 Database Optimization'))
        self.stdout.write('=' * 50)
        
        if options['all'] or options['apply_indexes']:
            self.apply_missing_indexes()
            
        if options['all'] or options['analyze_vacuum']:
            self.analyze_vacuum_db()

    def apply_missing_indexes(self):
        """Apply missing indexes for better performance."""
        self.stdout.write('\n📈 APPLYING MISSING INDEXES')
        self.stdout.write('-' * 40)
        
        indexes_to_create = [
            # Critical foreign key indexes
            {
                'name': 'idx_medicine_appointments_doctor_id',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_medicine_appointments_doctor_id ON medicine_appointments(doctor_id);',
                'description': 'Index on medicine appointments doctor_id'
            },
            {
                'name': 'idx_medicine_appointments_patient_id',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_medicine_appointments_patient_id ON medicine_appointments(patient_id);',
                'description': 'Index on medicine appointments patient_id'
            },
            {
                'name': 'idx_diabetes_glucose_patient_date',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diabetes_glucose_patient_date ON blood_glucose_readings(diabetes_patient_id, reading_date DESC);',
                'description': 'Composite index for glucose readings by patient and date'
            },
            {
                'name': 'idx_hba1c_patient_date',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_hba1c_patient_date ON hba1c_records(diabetes_patient_id, test_date DESC);',
                'description': 'Composite index for HbA1c records by patient and date'
            },
            {
                'name': 'idx_medicine_medical_records_patient',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_medicine_medical_records_patient ON medicine_medical_records(patient_id);',
                'description': 'Index on medical records patient_id'
            },
            {
                'name': 'idx_medicine_prescriptions_patient',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_medicine_prescriptions_patient ON medicine_prescriptions(patient_id);',
                'description': 'Index on prescriptions patient_id'
            },
            {
                'name': 'idx_diabetes_medications_patient',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diabetes_medications_patient ON diabetes_medications(diabetes_patient_id);',
                'description': 'Index on diabetes medications patient_id'
            },
            {
                'name': 'idx_subscriptions_user',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_user ON subscriptions_usersubscription(user_id);',
                'description': 'Index on user subscriptions'
            },
        ]
        
        with connection.cursor() as cursor:
            for index_info in indexes_to_create:
                try:
                    self.stdout.write(f'Creating {index_info["name"]}...', ending='')
                    start_time = time.time()
                    
                    cursor.execute(index_info['sql'])
                    
                    elapsed = time.time() - start_time
                    self.stdout.write(self.style.SUCCESS(f' ✅ ({elapsed:.2f}s)'))
                    
                except Exception as e:
                    if 'already exists' in str(e):
                        self.stdout.write(self.style.WARNING(' ⚠️ Already exists'))
                    else:
                        self.stdout.write(self.style.ERROR(f' ❌ Error: {str(e)}'))

    def analyze_vacuum_db(self):
        """Run ANALYZE and VACUUM on database."""
        self.stdout.write('\n🔧 DATABASE MAINTENANCE')
        self.stdout.write('-' * 40)
        
        with connection.cursor() as cursor:
            # Get list of user tables
            cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT LIKE 'django_%'
                ORDER BY tablename;
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write(f'Analyzing {len(tables)} tables...')
            
            for table in tables:
                try:
                    self.stdout.write(f'  Analyzing {table}...', ending='')
                    start_time = time.time()
                    
                    # ANALYZE to update statistics
                    cursor.execute(f'ANALYZE "{table}";')
                    
                    elapsed = time.time() - start_time
                    self.stdout.write(f' ✅ ({elapsed:.3f}s)')
                    
                except Exception as e:
                    self.stdout.write(f' ❌ Error: {str(e)}')
            
            # Run VACUUM (cleanup)
            try:
                self.stdout.write('Running VACUUM...', ending='')
                start_time = time.time()
                
                cursor.execute('VACUUM;')
                
                elapsed = time.time() - start_time
                self.stdout.write(self.style.SUCCESS(f' ✅ ({elapsed:.2f}s)'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f' ❌ Error: {str(e)}'))
                
        self.stdout.write(f'\n✅ Database optimization complete!')
