"""
Medicine S3 Data Manager Service

Hierarchical AWS S3 storage system for Medicine department with comprehensive
data management, encryption, and HIPAA compliance.

Directory Structure:
medicine/
├── institutions/
│   └── {institution_id}/
│       ├── patients/
│       │   └── {patient_id}/
│       │       ├── medical_records/
│       │       ├── lab_results/
│       │       ├── prescriptions/
│       │       ├── treatment_plans/
│       │       ├── diagnostic_images/
│       │       └── consultation_notes/
│       └── analytics/
"""

import os
import boto3
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from botocore.exceptions import ClientError, NoCredentialsError
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.cache import cache

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class MedicineFileMetadata:
    """Metadata for medicine files stored in S3."""
    file_key: str
    file_type: str  # medical_record, lab_result, prescription, treatment_plan, diagnostic_image, consultation_note
    file_size: int
    upload_date: datetime
    encrypted: bool
    patient_id: str
    doctor_id: Optional[str] = None
    consultation_id: Optional[str] = None
    lab_test_id: Optional[str] = None
    prescription_id: Optional[str] = None

@dataclass
class MedicineStorageStats:
    """Storage statistics for medicine data."""
    total_files: int
    total_size_mb: float
    files_by_type: Dict[str, int]
    size_by_type: Dict[str, float]
    recent_uploads: List[MedicineFileMetadata]
    storage_usage_percentage: float

class MedicineS3DataManager:
    """
    Comprehensive S3 data management system for Medicine department.
    
    Features:
    - Hierarchical folder structure for medical data organization
    - AES encryption for sensitive patient information
    - HIPAA compliant audit logging
    - Medical record lifecycle management
    - Lab result and prescription storage
    - Treatment plan and consultation note management
    - Diagnostic image storage with metadata
    - Analytics and reporting capabilities
    """
    
    def __init__(self):
        """Initialize the Medicine S3 Data Manager."""
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'alfiya-medical-data')
        self.region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY'),
                region_name=self.region
            )
            logger.info("Medicine S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
        
        # Initialize encryption
        self._init_encryption()
        
        # Base prefix for medicine data
        self.base_prefix = "medicine/"
        
        # File type mappings
        self.file_types = {
            'medical_record': {
                'folder': 'medical_records',
                'extensions': ['.pdf', '.doc', '.docx', '.txt'],
                'max_size_mb': 50
            },
            'lab_result': {
                'folder': 'lab_results',
                'extensions': ['.pdf', '.jpg', '.png', '.csv', '.xlsx'],
                'max_size_mb': 25
            },
            'prescription': {
                'folder': 'prescriptions',
                'extensions': ['.pdf', '.doc', '.docx', '.jpg', '.png'],
                'max_size_mb': 10
            },
            'treatment_plan': {
                'folder': 'treatment_plans',
                'extensions': ['.pdf', '.doc', '.docx'],
                'max_size_mb': 20
            },
            'diagnostic_image': {
                'folder': 'diagnostic_images',
                'extensions': ['.jpg', '.png', '.tiff', '.dcm', '.nii'],
                'max_size_mb': 100
            },
            'consultation_note': {
                'folder': 'consultation_notes',
                'extensions': ['.pdf', '.doc', '.docx', '.txt'],
                'max_size_mb': 15
            }
        }
    
    def _init_encryption(self):
        """Initialize encryption for sensitive data."""
        try:
            encryption_key = getattr(settings, 'MEDICINE_ENCRYPTION_KEY', None)
            if not encryption_key:
                # Generate new key if not exists
                encryption_key = Fernet.generate_key()
                logger.warning("Generated new encryption key. Store this securely!")
                print(f"Generated new encryption key. Store this securely!")
            
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            
            self.cipher_suite = Fernet(encryption_key)
            logger.info("Medicine encryption initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self.cipher_suite = None
    
    def create_institution_structure(self, institution_id: str, institution_name: str) -> Dict[str, Any]:
        """
        Create S3 folder structure for a new medical institution.
        
        Args:
            institution_id: Unique identifier for the institution
            institution_name: Name of the institution
            
        Returns:
            Dict containing creation status and paths
        """
        try:
            institution_prefix = f"{self.base_prefix}institutions/{institution_id}/"
            
            # Create institution folders
            folders_to_create = [
                f"{institution_prefix}patients/",
                f"{institution_prefix}analytics/",
                f"{institution_prefix}reports/",
                f"{institution_prefix}staff/",
                f"{institution_prefix}inventory/"
            ]
            
            for folder in folders_to_create:
                self._create_s3_folder(folder)
            
            # Create institution metadata
            institution_metadata = {
                'institution_id': institution_id,
                'institution_name': institution_name,
                'created_at': datetime.now().isoformat(),
                'folder_structure': folders_to_create,
                'total_patients': 0,
                'total_records': 0
            }
            
            # Store metadata
            metadata_key = f"{institution_prefix}metadata.json"
            self._upload_json_data(metadata_key, institution_metadata)
            
            logger.info(f"Created institution structure for {institution_name}")
            
            return {
                'success': True,
                'institution_prefix': institution_prefix,
                'folders_created': folders_to_create,
                'metadata_key': metadata_key
            }
            
        except Exception as e:
            logger.error(f"Error creating institution structure: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_patient_directory(self, institution_id: str, patient_id: str, 
                               patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comprehensive S3 directory structure for a new patient.
        
        Args:
            institution_id: Institution identifier
            patient_id: Unique patient identifier
            patient_info: Patient information dictionary
            
        Returns:
            Dict containing creation status and patient structure
        """
        try:
            patient_prefix = f"{self.base_prefix}institutions/{institution_id}/patients/{patient_id}/"
            
            # Create patient-specific folders
            patient_folders = []
            for file_type, config in self.file_types.items():
                folder_path = f"{patient_prefix}{config['folder']}/"
                patient_folders.append(folder_path)
                self._create_s3_folder(folder_path)
            
            # Additional patient folders
            additional_folders = [
                f"{patient_prefix}profile/",
                f"{patient_prefix}appointments/",
                f"{patient_prefix}billing/",
                f"{patient_prefix}insurance/",
                f"{patient_prefix}emergency_contacts/"
            ]
            
            for folder in additional_folders:
                patient_folders.append(folder)
                self._create_s3_folder(folder)
            
            # Encrypt sensitive patient information
            encrypted_patient_info = patient_info.copy()
            if self.cipher_suite:
                sensitive_fields = ['ssn', 'insurance_number', 'emergency_contact', 'address']
                for field in sensitive_fields:
                    if field in encrypted_patient_info:
                        encrypted_data = self.cipher_suite.encrypt(
                            str(encrypted_patient_info[field]).encode()
                        )
                        encrypted_patient_info[field] = encrypted_data.decode()
            
            # Create patient profile metadata
            patient_metadata = {
                'patient_id': patient_id,
                'institution_id': institution_id,
                'created_at': datetime.now().isoformat(),
                'patient_info': encrypted_patient_info,
                'folder_structure': patient_folders,
                'total_records': 0,
                'last_visit': None,
                's3_patient_prefix': patient_prefix
            }
            
            # Store patient metadata
            metadata_key = f"{patient_prefix}profile/patient_metadata.json"
            self._upload_json_data(metadata_key, patient_metadata)
            
            # Log audit trail
            self._log_audit_action(
                action='create_patient',
                resource_type='patient_directory',
                resource_id=patient_id,
                details={'institution_id': institution_id, 'folders_created': len(patient_folders)}
            )
            
            logger.info(f"Created patient directory for patient {patient_id}")
            
            return {
                'success': True,
                'patient_prefix': patient_prefix,
                'folders_created': patient_folders,
                'metadata_key': metadata_key,
                'encrypted_fields': len([f for f in ['ssn', 'insurance_number', 'emergency_contact', 'address'] if f in patient_info])
            }
            
        except Exception as e:
            logger.error(f"Error creating patient directory: {e}")
            return {'success': False, 'error': str(e)}
    
    def upload_medical_record(self, institution_id: str, patient_id: str, 
                            file_content: bytes, filename: str, file_type: str,
                            metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload a medical record to patient's S3 directory.
        
        Args:
            institution_id: Institution identifier
            patient_id: Patient identifier
            file_content: File content as bytes
            filename: Original filename
            file_type: Type of medical file
            metadata: Additional metadata
            
        Returns:
            Dict containing upload status and file information
        """
        try:
            if file_type not in self.file_types:
                return {'success': False, 'error': f'Invalid file type: {file_type}'}
            
            # Validate file size
            file_size_mb = len(file_content) / (1024 * 1024)
            max_size = self.file_types[file_type]['max_size_mb']
            if file_size_mb > max_size:
                return {'success': False, 'error': f'File size exceeds {max_size}MB limit'}
            
            # Generate unique filename
            file_extension = os.path.splitext(filename)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Determine S3 key
            folder = self.file_types[file_type]['folder']
            s3_key = f"{self.base_prefix}institutions/{institution_id}/patients/{patient_id}/{folder}/{unique_filename}"
            
            # Encrypt file content if sensitive
            if file_type in ['medical_record', 'lab_result', 'prescription'] and self.cipher_suite:
                encrypted_content = self.cipher_suite.encrypt(file_content)
                upload_content = encrypted_content
                encrypted = True
            else:
                upload_content = file_content
                encrypted = False
            
            # Create file metadata
            file_metadata = MedicineFileMetadata(
                file_key=s3_key,
                file_type=file_type,
                file_size=len(file_content),
                upload_date=datetime.now(),
                encrypted=encrypted,
                patient_id=patient_id,
                doctor_id=metadata.get('doctor_id') if metadata else None,
                consultation_id=metadata.get('consultation_id') if metadata else None,
                lab_test_id=metadata.get('lab_test_id') if metadata else None,
                prescription_id=metadata.get('prescription_id') if metadata else None
            )
            
            # Upload to S3
            upload_result = self._upload_file_to_s3(s3_key, upload_content, {
                'original_filename': filename,
                'file_type': file_type,
                'patient_id': patient_id,
                'institution_id': institution_id,
                'encrypted': str(encrypted),
                'upload_date': datetime.now().isoformat()
            })
            
            if upload_result['success']:
                # Store file metadata
                metadata_key = f"{s3_key}.metadata.json"
                self._upload_json_data(metadata_key, file_metadata.__dict__)
                
                # Log audit trail
                self._log_audit_action(
                    action='upload_medical_record',
                    resource_type=file_type,
                    resource_id=s3_key,
                    details={
                        'patient_id': patient_id,
                        'institution_id': institution_id,
                        'file_size_mb': round(file_size_mb, 2),
                        'encrypted': encrypted
                    }
                )
                
                logger.info(f"Uploaded {file_type} for patient {patient_id}")
                
                return {
                    'success': True,
                    's3_key': s3_key,
                    'file_metadata': file_metadata.__dict__,
                    'encrypted': encrypted,
                    'file_size_mb': round(file_size_mb, 2)
                }
            else:
                return upload_result
                
        except Exception as e:
            logger.error(f"Error uploading medical record: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_treatment_plan(self, institution_id: str, patient_id: str,
                            treatment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and store a comprehensive treatment plan.
        
        Args:
            institution_id: Institution identifier
            patient_id: Patient identifier
            treatment_data: Treatment plan information
            
        Returns:
            Dict containing creation status and treatment plan details
        """
        try:
            treatment_id = str(uuid.uuid4())
            treatment_key = f"{self.base_prefix}institutions/{institution_id}/patients/{patient_id}/treatment_plans/plan_{treatment_id}.json"
            
            # Create comprehensive treatment plan
            treatment_plan = {
                'treatment_id': treatment_id,
                'patient_id': patient_id,
                'institution_id': institution_id,
                'created_at': datetime.now().isoformat(),
                'created_by': treatment_data.get('doctor_id'),
                'diagnosis': treatment_data.get('diagnosis'),
                'treatment_goals': treatment_data.get('treatment_goals', []),
                'medications': treatment_data.get('medications', []),
                'procedures': treatment_data.get('procedures', []),
                'follow_up_schedule': treatment_data.get('follow_up_schedule', []),
                'dietary_recommendations': treatment_data.get('dietary_recommendations'),
                'lifestyle_modifications': treatment_data.get('lifestyle_modifications'),
                'expected_duration': treatment_data.get('expected_duration'),
                'progress_indicators': treatment_data.get('progress_indicators', []),
                'emergency_protocols': treatment_data.get('emergency_protocols'),
                'status': 'active',
                'last_updated': datetime.now().isoformat()
            }
            
            # Encrypt sensitive treatment information
            if self.cipher_suite:
                sensitive_fields = ['diagnosis', 'medications', 'emergency_protocols']
                for field in sensitive_fields:
                    if field in treatment_plan and treatment_plan[field]:
                        encrypted_data = self.cipher_suite.encrypt(
                            json.dumps(treatment_plan[field]).encode()
                        )
                        treatment_plan[f'{field}_encrypted'] = encrypted_data.decode()
                        treatment_plan[field] = '[ENCRYPTED]'
            
            # Upload treatment plan
            upload_result = self._upload_json_data(treatment_key, treatment_plan)
            
            if upload_result['success']:
                # Log audit trail
                self._log_audit_action(
                    action='create_treatment_plan',
                    resource_type='treatment_plan',
                    resource_id=treatment_id,
                    details={
                        'patient_id': patient_id,
                        'institution_id': institution_id,
                        'doctor_id': treatment_data.get('doctor_id'),
                        'diagnosis': treatment_data.get('diagnosis', '')[:50] + '...' if len(treatment_data.get('diagnosis', '')) > 50 else treatment_data.get('diagnosis', '')
                    }
                )
                
                logger.info(f"Created treatment plan {treatment_id} for patient {patient_id}")
                
                return {
                    'success': True,
                    'treatment_id': treatment_id,
                    's3_key': treatment_key,
                    'treatment_plan': treatment_plan
                }
            else:
                return upload_result
                
        except Exception as e:
            logger.error(f"Error creating treatment plan: {e}")
            return {'success': False, 'error': str(e)}
    
    def store_lab_results(self, institution_id: str, patient_id: str,
                         lab_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store comprehensive lab results with analysis.
        
        Args:
            institution_id: Institution identifier
            patient_id: Patient identifier
            lab_data: Lab results and metadata
            
        Returns:
            Dict containing storage status and lab result details
        """
        try:
            lab_id = str(uuid.uuid4())
            lab_key = f"{self.base_prefix}institutions/{institution_id}/patients/{patient_id}/lab_results/lab_{lab_id}.json"
            
            # Create comprehensive lab results
            lab_results = {
                'lab_id': lab_id,
                'patient_id': patient_id,
                'institution_id': institution_id,
                'test_date': lab_data.get('test_date', datetime.now().isoformat()),
                'ordered_by': lab_data.get('doctor_id'),
                'lab_facility': lab_data.get('lab_facility'),
                'test_type': lab_data.get('test_type'),
                'test_category': lab_data.get('test_category'),  # blood, urine, microbiology, etc.
                'test_results': lab_data.get('test_results', {}),
                'reference_ranges': lab_data.get('reference_ranges', {}),
                'abnormal_flags': lab_data.get('abnormal_flags', []),
                'critical_values': lab_data.get('critical_values', []),
                'interpretation': lab_data.get('interpretation'),
                'recommendations': lab_data.get('recommendations'),
                'status': lab_data.get('status', 'final'),
                'verified_by': lab_data.get('verified_by'),
                'created_at': datetime.now().isoformat(),
                'fasting_status': lab_data.get('fasting_status'),
                'specimen_type': lab_data.get('specimen_type'),
                'collection_method': lab_data.get('collection_method')
            }
            
            # Encrypt sensitive lab results
            if self.cipher_suite:
                sensitive_fields = ['test_results', 'critical_values', 'interpretation']
                for field in sensitive_fields:
                    if field in lab_results and lab_results[field]:
                        encrypted_data = self.cipher_suite.encrypt(
                            json.dumps(lab_results[field]).encode()
                        )
                        lab_results[f'{field}_encrypted'] = encrypted_data.decode()
                        lab_results[field] = '[ENCRYPTED]'
            
            # Upload lab results
            upload_result = self._upload_json_data(lab_key, lab_results)
            
            if upload_result['success']:
                # Log audit trail
                self._log_audit_action(
                    action='store_lab_results',
                    resource_type='lab_results',
                    resource_id=lab_id,
                    details={
                        'patient_id': patient_id,
                        'institution_id': institution_id,
                        'test_type': lab_data.get('test_type'),
                        'test_date': lab_data.get('test_date'),
                        'abnormal_flags_count': len(lab_data.get('abnormal_flags', [])),
                        'critical_values_count': len(lab_data.get('critical_values', []))
                    }
                )
                
                logger.info(f"Stored lab results {lab_id} for patient {patient_id}")
                
                return {
                    'success': True,
                    'lab_id': lab_id,
                    's3_key': lab_key,
                    'lab_results': lab_results
                }
            else:
                return upload_result
                
        except Exception as e:
            logger.error(f"Error storing lab results: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_patient_medical_summary(self, institution_id: str, patient_id: str) -> Dict[str, Any]:
        """
        Get comprehensive medical summary for a patient.
        
        Args:
            institution_id: Institution identifier
            patient_id: Patient identifier
            
        Returns:
            Dict containing patient's complete medical summary
        """
        try:
            patient_prefix = f"{self.base_prefix}institutions/{institution_id}/patients/{patient_id}/"
            
            # Get all files for this patient
            patient_files = self._list_s3_objects(patient_prefix)
            
            summary = {
                'patient_id': patient_id,
                'institution_id': institution_id,
                'total_files': len(patient_files),
                'files_by_type': {},
                'recent_activity': [],
                'storage_usage_mb': 0,
                'last_updated': None
            }
            
            # Analyze files by type
            for file_obj in patient_files:
                file_key = file_obj['Key']
                file_size_mb = file_obj['Size'] / (1024 * 1024)
                summary['storage_usage_mb'] += file_size_mb
                
                # Determine file type from path
                for file_type, config in self.file_types.items():
                    if config['folder'] in file_key:
                        if file_type not in summary['files_by_type']:
                            summary['files_by_type'][file_type] = {
                                'count': 0,
                                'size_mb': 0,
                                'recent_files': []
                            }
                        summary['files_by_type'][file_type]['count'] += 1
                        summary['files_by_type'][file_type]['size_mb'] += file_size_mb
                        
                        if len(summary['files_by_type'][file_type]['recent_files']) < 5:
                            summary['files_by_type'][file_type]['recent_files'].append({
                                'file_key': file_key,
                                'size_mb': round(file_size_mb, 2),
                                'last_modified': file_obj['LastModified'].isoformat()
                            })
                        break
                
                # Track recent activity
                if len(summary['recent_activity']) < 10:
                    summary['recent_activity'].append({
                        'file_key': file_key,
                        'action': 'upload',
                        'timestamp': file_obj['LastModified'].isoformat(),
                        'size_mb': round(file_size_mb, 2)
                    })
            
            # Sort recent activity by timestamp
            summary['recent_activity'].sort(key=lambda x: x['timestamp'], reverse=True)
            summary['recent_activity'] = summary['recent_activity'][:10]
            
            if summary['recent_activity']:
                summary['last_updated'] = summary['recent_activity'][0]['timestamp']
            
            summary['storage_usage_mb'] = round(summary['storage_usage_mb'], 2)
            
            logger.info(f"Generated medical summary for patient {patient_id}")
            
            return {
                'success': True,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error generating patient medical summary: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_medicine_analytics(self, institution_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for medicine department.
        
        Args:
            institution_id: Institution identifier
            
        Returns:
            Dict containing detailed analytics and metrics
        """
        try:
            institution_prefix = f"{self.base_prefix}institutions/{institution_id}/"
            
            # Get all files for this institution
            all_files = self._list_s3_objects(institution_prefix)
            
            analytics = {
                'institution_id': institution_id,
                'total_files': len(all_files),
                'total_storage_gb': 0,
                'patients_count': 0,
                'files_by_type': {},
                'storage_by_type': {},
                'monthly_uploads': {},
                'patient_activity': {},
                'top_file_types': [],
                'storage_growth': [],
                'generated_at': datetime.now().isoformat()
            }
            
            patient_ids = set()
            
            # Analyze all files
            for file_obj in all_files:
                file_key = file_obj['Key']
                file_size_gb = file_obj['Size'] / (1024 * 1024 * 1024)
                analytics['total_storage_gb'] += file_size_gb
                
                # Extract patient ID from path
                path_parts = file_key.split('/')
                if 'patients' in path_parts:
                    try:
                        patient_idx = path_parts.index('patients')
                        if patient_idx + 1 < len(path_parts):
                            patient_id = path_parts[patient_idx + 1]
                            patient_ids.add(patient_id)
                            
                            # Track patient activity
                            if patient_id not in analytics['patient_activity']:
                                analytics['patient_activity'][patient_id] = {
                                    'files': 0,
                                    'storage_gb': 0,
                                    'last_activity': None
                                }
                            
                            analytics['patient_activity'][patient_id]['files'] += 1
                            analytics['patient_activity'][patient_id]['storage_gb'] += file_size_gb
                            
                            file_date = file_obj['LastModified'].isoformat()
                            if (analytics['patient_activity'][patient_id]['last_activity'] is None or 
                                file_date > analytics['patient_activity'][patient_id]['last_activity']):
                                analytics['patient_activity'][patient_id]['last_activity'] = file_date
                    except (ValueError, IndexError):
                        pass
                
                # Analyze by file type
                for file_type, config in self.file_types.items():
                    if config['folder'] in file_key:
                        if file_type not in analytics['files_by_type']:
                            analytics['files_by_type'][file_type] = 0
                            analytics['storage_by_type'][file_type] = 0
                        
                        analytics['files_by_type'][file_type] += 1
                        analytics['storage_by_type'][file_type] += file_size_gb
                        break
                
                # Monthly upload analysis
                upload_month = file_obj['LastModified'].strftime('%Y-%m')
                if upload_month not in analytics['monthly_uploads']:
                    analytics['monthly_uploads'][upload_month] = {
                        'files': 0,
                        'storage_gb': 0
                    }
                analytics['monthly_uploads'][upload_month]['files'] += 1
                analytics['monthly_uploads'][upload_month]['storage_gb'] += file_size_gb
            
            analytics['patients_count'] = len(patient_ids)
            analytics['total_storage_gb'] = round(analytics['total_storage_gb'], 3)
            
            # Create top file types ranking
            analytics['top_file_types'] = [
                {
                    'type': file_type,
                    'count': count,
                    'storage_gb': round(analytics['storage_by_type'].get(file_type, 0), 3),
                    'percentage': round((count / analytics['total_files']) * 100, 1) if analytics['total_files'] > 0 else 0
                }
                for file_type, count in sorted(analytics['files_by_type'].items(), key=lambda x: x[1], reverse=True)
            ]
            
            # Round storage values
            for file_type in analytics['storage_by_type']:
                analytics['storage_by_type'][file_type] = round(analytics['storage_by_type'][file_type], 3)
            
            for patient_id in analytics['patient_activity']:
                analytics['patient_activity'][patient_id]['storage_gb'] = round(
                    analytics['patient_activity'][patient_id]['storage_gb'], 3
                )
            
            logger.info(f"Generated medicine analytics for institution {institution_id}")
            
            return {
                'success': True,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error generating medicine analytics: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_s3_folder(self, folder_path: str) -> bool:
        """Create an S3 folder by uploading an empty object."""
        try:
            if not folder_path.endswith('/'):
                folder_path += '/'
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=folder_path,
                Body=b''
            )
            return True
        except Exception as e:
            logger.error(f"Error creating S3 folder {folder_path}: {e}")
            return False
    
    def _upload_file_to_s3(self, s3_key: str, file_content: bytes, 
                          metadata: Dict[str, str]) -> Dict[str, Any]:
        """Upload file to S3 with metadata."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                Metadata=metadata,
                ServerSideEncryption='AES256'
            )
            
            return {
                'success': True,
                's3_key': s3_key,
                'bucket': self.bucket_name
            }
            
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            return {'success': False, 'error': str(e)}
    
    def _upload_json_data(self, s3_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload JSON data to S3."""
        try:
            json_content = json.dumps(data, indent=2, default=str)
            return self._upload_file_to_s3(s3_key, json_content.encode(), {
                'content_type': 'application/json',
                'created_at': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error uploading JSON data: {e}")
            return {'success': False, 'error': str(e)}
    
    def _list_s3_objects(self, prefix: str) -> List[Dict[str, Any]]:
        """List all objects with given prefix."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            return response.get('Contents', [])
        except Exception as e:
            logger.error(f"Error listing S3 objects: {e}")
            return []
    
    def _log_audit_action(self, action: str, resource_type: str, 
                         resource_id: str, details: Dict[str, Any]) -> None:
        """Log audit trail for compliance."""
        try:
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details,
                'service': 'medicine_s3_manager'
            }
            
            # Store in cache for recent activity
            cache_key = f"medicine_audit_{datetime.now().strftime('%Y%m%d')}"
            audit_log = cache.get(cache_key, [])
            audit_log.append(audit_entry)
            cache.set(cache_key, audit_log[-100:], 86400)  # Keep last 100 entries for 24 hours
            
            logger.info(f"Audit logged: {action} on {resource_type} {resource_id}")
            
        except Exception as e:
            logger.error(f"Error logging audit action: {e}")


# Global instance
medicine_s3_manager = MedicineS3DataManager()
