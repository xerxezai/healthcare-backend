"""
Django management command to analyze database performance and structure
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.apps import apps
from django.db.models import Count
import time


class Command(BaseCommand):
    """Django command to analyze database."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze-tables',
            action='store_true',
            help='Analyze table sizes and row counts',
        )
        parser.add_argument(
            '--analyze-indexes',
            action='store_true',
            help='Analyze database indexes',
        )
        parser.add_argument(
            '--analyze-performance',
            action='store_true',
            help='Analyze database performance',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all analyses',
        )

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write(self.style.SUCCESS('🔍 Database Analysis Report'))
        self.stdout.write('=' * 60)
        
        if options['all'] or options['analyze_tables']:
            self.analyze_tables()
            
        if options['all'] or options['analyze_indexes']:
            self.analyze_indexes()
            
        if options['all'] or options['analyze_performance']:
            self.analyze_performance()

    def analyze_tables(self):
        """Analyze table sizes and row counts."""
        self.stdout.write('\n📊 TABLE ANALYSIS')
        self.stdout.write('-' * 40)
        
        # Get all models
        all_models = apps.get_models()
        
        for model in all_models:
            try:
                count = model.objects.count()
                table_name = model._meta.db_table
                self.stdout.write(f'{table_name:<40} | {count:>8} rows')
            except Exception as e:
                self.stdout.write(f'{model._meta.db_table:<40} | Error: {str(e)}')

    def analyze_indexes(self):
        """Analyze database indexes."""
        self.stdout.write('\n🗂️  INDEX ANALYSIS')
        self.stdout.write('-' * 40)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    relname as tablename,
                    indexrelname as indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC
                LIMIT 20;
            """)
            
            self.stdout.write(f'{"Table":<30} | {"Index":<30} | {"Scans":<8} | {"Reads":<10}')
            self.stdout.write('-' * 80)
            
            for row in cursor.fetchall():
                schema, table, index, scans, reads, fetches = row
                self.stdout.write(f'{table:<30} | {index:<30} | {scans or 0:<8} | {reads or 0:<10}')

    def analyze_performance(self):
        """Analyze database performance."""
        self.stdout.write('\n⚡ PERFORMANCE ANALYSIS')
        self.stdout.write('-' * 40)
        
        with connection.cursor() as cursor:
            # Database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
            db_size = cursor.fetchone()[0]
            self.stdout.write(f'Database Size: {db_size}')
            
            # Connection info
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            self.stdout.write(f'PostgreSQL Version: {version.split(",")[0]}')
            
            # Table sizes
            cursor.execute("""
                SELECT 
                    relname AS table_name,
                    pg_size_pretty(pg_total_relation_size(relid)) AS size
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(relid) DESC
                LIMIT 10;
            """)
            
            self.stdout.write(f'\n📈 LARGEST TABLES:')
            self.stdout.write(f'{"Table":<40} | {"Size":<15}')
            self.stdout.write('-' * 60)
            
            for row in cursor.fetchall():
                table, size = row
                self.stdout.write(f'{table:<40} | {size:<15}')
                
            # Check for missing indexes on foreign keys
            cursor.execute("""
                SELECT 
                    t.relname AS table_name,
                    a.attname AS column_name,
                    'Missing index on foreign key' AS recommendation
                FROM pg_constraint c
                JOIN pg_class t ON c.conrelid = t.oid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(c.conkey)
                WHERE c.contype = 'f'
                AND NOT EXISTS (
                    SELECT 1 FROM pg_index i
                    WHERE i.indrelid = t.oid
                    AND a.attnum = ANY(i.indkey)
                )
                ORDER BY t.relname, a.attname
                LIMIT 10;
            """)
            
            missing_indexes = cursor.fetchall()
            if missing_indexes:
                self.stdout.write(f'\n⚠️  POTENTIAL MISSING INDEXES:')
                self.stdout.write(f'{"Table":<40} | {"Column":<30}')
                self.stdout.write('-' * 75)
                for row in missing_indexes:
                    table, column, _ = row
                    self.stdout.write(f'{table:<40} | {column:<30}')
            else:
                self.stdout.write(f'\n✅ All foreign keys appear to have indexes')
                
        self.stdout.write(f'\n✅ Database analysis complete!')
