import os
import sys
import django
from io import StringIO

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.core.management import call_command

# Mock input for migrations
old_input = input
def mock_input(prompt=""):
    if "Select an option" in prompt:
        return "1"
    elif "[default: timezone.now]" in prompt:
        return ""  # Accept default
    return ""

# Replace input temporarily
import builtins
builtins.input = mock_input

try:
    # Create migrations
    call_command('makemigrations', verbosity=2)
    print("✅ Migrations created successfully!")
    
    # Apply migrations
    call_command('migrate', verbosity=2)
    print("✅ Migrations applied successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")

finally:
    # Restore original input
    builtins.input = old_input
