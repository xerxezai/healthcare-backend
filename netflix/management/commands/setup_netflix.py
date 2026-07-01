"""
Management command to setup initial Netflix data including genres and default roles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from netflix.models import Genre, EnhancedRole, UserEntitlements

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup initial Netflix data including genres and roles'
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up initial Netflix data...')
        
        # Create default genres
        genres_data = [
            'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary',
            'Drama', 'Family', 'Fantasy', 'History', 'Horror', 'Music',
            'Mystery', 'Romance', 'Science Fiction', 'Thriller', 'War', 'Western'
        ]
        
        for genre_name in genres_data:
            genre, created = Genre.objects.get_or_create(name=genre_name)
            if created:
                self.stdout.write(f'Created genre: {genre_name}')
        
        # Create default roles
        roles_data = [
            {
                'name': 'Content Manager',
                'role_type': 'CONTENT_MANAGER',
                'description': 'Can manage all content including titles, seasons, episodes, and assets',
                'scopes': {
                    'content': ['read', 'write', 'delete'],
                    'assets': ['read', 'write', 'delete'],
                    'audit': ['read']
                }
            },
            {
                'name': 'Finance Manager',
                'role_type': 'FINANCE_OPS',
                'description': 'Can manage payments, invoices, and user entitlements',
                'scopes': {
                    'finance': ['read', 'write'],
                    'entitlements': ['read', 'write'],
                    'audit': ['read']
                }
            },
            {
                'name': 'User Manager',
                'role_type': 'USER_SUPPORT',
                'description': 'Can manage user profiles, devices, and roles',
                'scopes': {
                    'profiles': ['read', 'write'],
                    'devices': ['read', 'write'],
                    'roles': ['read', 'write'],
                    'entitlements': ['read'],
                    'audit': ['read']
                }
            },
            {
                'name': 'Viewer',
                'role_type': 'ADMIN_CUSTOM',
                'description': 'Basic viewer permissions for content consumption',
                'scopes': {
                    'content': ['read'],
                    'watchlist': ['read', 'write'],
                    'history': ['read'],
                    'ratings': ['read', 'write']
                }
            },
            {
                'name': 'Administrator',
                'role_type': 'SUPER_ADMIN',
                'description': 'Full system access',
                'scopes': {
                    'content': ['all'],
                    'assets': ['all'],
                    'profiles': ['all'],
                    'devices': ['all'],
                    'finance': ['all'],
                    'entitlements': ['all'],
                    'roles': ['all'],
                    'audit': ['all'],
                    'watchlist': ['all'],
                    'history': ['all'],
                    'ratings': ['all']
                }
            }
        ]
        
        # Get or create a superuser to assign as creator
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            self.stdout.write('No superuser found. Creating roles without creator assignment.')
        
        for role_data in roles_data:
            role, created = EnhancedRole.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'role_type': role_data['role_type'],
                    'description': role_data['description'],
                    'scopes': role_data['scopes'],
                    'created_by': superuser
                }
            )
            if created:
                self.stdout.write(f'Created role: {role_data["name"]}')
        
        # Ensure all existing users have entitlements
        users_without_entitlements = User.objects.filter(netflix_entitlements__isnull=True)
        for user in users_without_entitlements:
            entitlements = UserEntitlements.objects.create(
                user=user,
                account_status='ACTIVE',
                stream_access=True,
                max_profiles=2,
                max_devices=2,
                hd_enabled=True,
                uhd_enabled=False,
                download_enabled=True,
                region_access=['US', 'CA', 'UK']
            )
            self.stdout.write(f'Created entitlements for user: {user.email}')
        
        self.stdout.write(self.style.SUCCESS('Netflix setup completed successfully!'))
