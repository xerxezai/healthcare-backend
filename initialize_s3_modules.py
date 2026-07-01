#!/usr/bin/env python
"""
Initialize S3 Medical Module Folders
Creates base folder structure for all medical specialties in AWS S3
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('D:/alfiya/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from secureneat.s3_secure_manager import SecureS3Manager
import boto3
from datetime import datetime

def initialize_s3_medical_modules():
    """Initialize base folder structure for all medical modules"""
    print("🏥 Initializing S3 Medical Module Folders")
    print("=" * 60)
    
    # Medical modules to initialize
    medical_modules = [
        'radiology',
        'medicine', 
        'dentistry',
        'dermatology',
        'pathology',
        'homeopathy',
        'allopathy',
        'cosmetology',
        'dna_sequencing',
        'secureneat'
    ]
    
    # Initialize S3 manager
    s3_manager = SecureS3Manager()
    
    for module in medical_modules:
        print(f"\n📁 Initializing {module.title()} module...")
        
        try:
            # Create base module structure
            base_folders = [
                f"healthcare/{module}/",
                f"healthcare/{module}/staff/",
                f"healthcare/{module}/staff/doctors/",
                f"healthcare/{module}/staff/admins/", 
                f"healthcare/{module}/staff/nurses/",
                f"healthcare/{module}/patients/",
                f"healthcare/{module}/shared/",
                f"healthcare/{module}/templates/",
                f"healthcare/{module}/reports/",
                f"healthcare/{module}/archive/"
            ]
            
            # Create each folder by uploading a .keep file
            for folder in base_folders:
                try:
                    s3_manager.s3_client.put_object(
                        Bucket=s3_manager.bucket_name,
                        Key=f"{folder}.keep",
                        Body=b'# Healthcare module structure placeholder',
                        ServerSideEncryption='AES256',
                        ContentType='text/plain',
                        Metadata={
                            'module': module,
                            'created_at': datetime.now().isoformat(),
                            'purpose': 'module_structure_initialization',
                            'access_level': 'restricted'
                        }
                    )
                    print(f"   ✅ Created: {folder}")
                    
                except Exception as e:
                    print(f"   ❌ Failed to create {folder}: {str(e)}")
            
            print(f"✅ {module.title()} module initialized successfully!")
            
        except Exception as e:
            print(f"❌ Failed to initialize {module} module: {str(e)}")
    
    print(f"\n🎉 S3 Medical Module Initialization Complete!")
    print("=" * 60)
    print("Your S3 bucket now has the following structure:")
    print("""
healthcare/
├── radiology/
│   ├── staff/
│   │   ├── doctors/
│   │   ├── admins/
│   │   └── nurses/
│   ├── patients/
│   ├── shared/
│   ├── templates/
│   ├── reports/
│   └── archive/
├── medicine/
├── dentistry/
├── dermatology/
├── pathology/
├── homeopathy/
├── allopathy/
├── cosmetology/
├── dna_sequencing/
└── secureneat/
    """)

def list_current_s3_structure():
    """List current S3 bucket structure"""
    print("\n🔍 Current S3 Bucket Structure:")
    print("-" * 40)
    
    try:
        s3_manager = SecureS3Manager()
        
        # List objects in bucket with healthcare/ prefix
        response = s3_manager.s3_client.list_objects_v2(
            Bucket=s3_manager.bucket_name,
            Prefix='healthcare/',
            Delimiter='/'
        )
        
        if 'CommonPrefixes' in response:
            print("📁 Found healthcare modules:")
            for prefix in response['CommonPrefixes']:
                module_name = prefix['Prefix'].replace('healthcare/', '').replace('/', '')
                if module_name:
                    print(f"   📂 {module_name}")
        else:
            print("❌ No healthcare modules found in S3")
            
        # Count total objects
        all_objects = s3_manager.s3_client.list_objects_v2(
            Bucket=s3_manager.bucket_name,
            Prefix='healthcare/'
        )
        
        if 'Contents' in all_objects:
            print(f"\n📊 Total objects in healthcare/: {len(all_objects['Contents'])}")
        else:
            print("\n📊 No objects found in healthcare/ prefix")
            
    except Exception as e:
        print(f"❌ Error listing S3 structure: {str(e)}")

if __name__ == '__main__':
    # First show current structure
    list_current_s3_structure()
    
    # Ask for confirmation
    response = input("\n🤔 Do you want to initialize all medical module folders? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        initialize_s3_medical_modules()
        
        # Show updated structure
        print("\n" + "="*60)
        list_current_s3_structure()
    else:
        print("❌ Initialization cancelled by user")
