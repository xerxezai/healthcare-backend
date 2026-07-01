"""
Secure S3 Data Management System for Healthcare
HIPAA-Compliant File Management with Role-Based Access Control
"""
import os
import boto3
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from cryptography.fernet import Fernet
import hashlib
import hmac

# Import models
from .models import UserWorkspace, PatientFolder, S3FileRecord, S3AuditLog, AccessPermission

User = get_user_model()
logger = logging.getLogger(__name__)

class SecureS3Manager:
    """
    HIPAA-Compliant S3 Data Manager
    Handles secure file operations with granular permissions
    """
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        )
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'mastermind-healthcare-data')
        self.encryption_key = getattr(settings, 'DATA_ENCRYPTION_KEY', Fernet.generate_key())
        self.cipher = Fernet(self.encryption_key)
        
        # Module folder structure
        self.module_folders = {
            'radiology': 'healthcare/radiology',
            'medicine': 'healthcare/medicine', 
            'dentistry': 'healthcare/dentistry',
            'dermatology': 'healthcare/dermatology',
            'pathology': 'healthcare/pathology',
            'homeopathy': 'healthcare/homeopathy',
            'allopathy': 'healthcare/allopathy',
            'cosmetology': 'healthcare/cosmetology',
            'dna_sequencing': 'research/dna-sequencing',
            'secureneat': 'education/secureneat',
            'netflix': 'entertainment/netflix'
        }
        
        # Role permissions matrix
        self.role_permissions = {
            'super_admin': {
                'read': ['*'],  # All modules
                'write': ['*'],
                'delete': ['*'],
                'admin': ['*']
            },
            'admin': {
                'read': [],  # Module-specific, set dynamically
                'write': [],
                'delete': [],
                'admin': []
            },
            'doctor': {
                'read': [],  # Only assigned patients
                'write': [],  # Only assigned patients
                'delete': [],  # Limited delete permissions
                'admin': []   # No admin permissions
            },
            'nurse': {
                'read': [],   # Assigned patients only
                'write': [],  # Limited write permissions
                'delete': [],
                'admin': []
            },
            'patient': {
                'read': [],   # Only their own data
                'write': [],  # Limited to personal uploads
                'delete': [],
                'admin': []
            }
        }

    def generate_secure_path(self, module: str, user_type: str, user_id: str, 
                           patient_id: str = None, file_type: str = 'general') -> str:
        """Generate HIPAA-compliant S3 path structure"""
        base_path = self.module_folders.get(module, f'healthcare/{module}')
        
        if user_type == 'doctor' or user_type == 'admin':
            # Doctor/Admin folder structure
            path = f"{base_path}/staff/{user_type}s/{user_id}"
            if patient_id:
                # Patient data under doctor/admin
                path += f"/patients/{patient_id}/{file_type}"
        elif user_type == 'patient':
            # Patient folder structure
            path = f"{base_path}/patients/{user_id}/{file_type}"
        else:
            # General staff
            path = f"{base_path}/staff/{user_type}s/{user_id}/{file_type}"
            
        return path

    def create_user_workspace(self, user: User, module: str, created_by: User = None) -> Dict[str, Any]:
        """Create secure workspace for user in S3"""
        try:
            user_path = self.generate_secure_path(
                module=module,
                user_type=user.role,
                user_id=str(user.id)
            )
            
            # Create directory structure
            folders = [
                f"{user_path}/documents/",
                f"{user_path}/reports/", 
                f"{user_path}/images/",
                f"{user_path}/temp/",
                f"{user_path}/archive/"
            ]
            
            # Create folders by uploading placeholder files
            for folder in folders:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=f"{folder}.keep",
                    Body=b'',
                    ServerSideEncryption='AES256',
                    Metadata={
                        'created_by': str(created_by.id) if created_by else str(user.id),
                        'created_at': datetime.now().isoformat(),
                        'module': module,
                        'access_level': 'restricted'
                    }
                )
            
            # Create workspace in database
            workspace, created = UserWorkspace.objects.get_or_create(
                user=user,
                module=module,
                defaults={
                    's3_path': user_path,
                    'storage_quota_gb': 10,  # Default 10GB
                    'status': 'active'
                }
            )
            
            # Log workspace creation
            self._log_action(
                user=user,
                action='workspace_created',
                module=module,
                details={'path': user_path, 'folders': len(folders)}
            )
            
            return {
                'success': True,
                'workspace_path': user_path,
                'workspace_id': str(workspace.id),
                'folders_created': folders,
                'message': f'Secure workspace created for {user.role} in {module}'
            }
            
        except Exception as e:
            logger.error(f"Failed to create workspace for user {user.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_patient_folder(self, doctor: User, patient_data: Dict[str, Any], 
                            module: str) -> Dict[str, Any]:
        """Create patient folder under doctor's workspace"""
        if doctor.role not in ['doctor', 'admin', 'super_admin']:
            raise PermissionDenied("Only doctors and admins can create patient folders")
            
        try:
            patient_id = patient_data.get('patient_id', str(uuid.uuid4()))
            
            # Generate patient path under doctor
            patient_path = self.generate_secure_path(
                module=module,
                user_type=doctor.role,
                user_id=str(doctor.id),
                patient_id=patient_id
            )
            
            # Create patient folder structure
            patient_folders = [
                f"{patient_path}/medical_records/",
                f"{patient_path}/lab_results/",
                f"{patient_path}/imaging/",
                f"{patient_path}/prescriptions/",
                f"{patient_path}/treatment_plans/",
                f"{patient_path}/progress_notes/",
                f"{patient_path}/discharge_summaries/",
                f"{patient_path}/consent_forms/"
            ]
            
            # Encrypt patient metadata
            encrypted_metadata = self._encrypt_patient_data(patient_data)
            
            # Create folders with encrypted metadata
            for folder in patient_folders:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=f"{folder}.keep",
                    Body=b'',
                    ServerSideEncryption='AES256',
                    Metadata={
                        'patient_id': patient_id,
                        'doctor_id': str(doctor.id),
                        'module': module,
                        'created_at': datetime.now().isoformat(),
                        'access_level': 'hipaa_protected',
                        'encrypted_metadata': encrypted_metadata
                    }
                )
            
            # Create patient index file
            patient_index = {
                'patient_id': patient_id,
                'created_by': str(doctor.id),
                'created_at': datetime.now().isoformat(),
                'module': module,
                'folder_structure': patient_folders,
                'access_permissions': self._generate_patient_permissions(doctor, patient_id)
            }
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f"{patient_path}/patient_index.json",
                Body=json.dumps(patient_index).encode(),
                ServerSideEncryption='AES256',
                ContentType='application/json'
            )
            
            # Log patient folder creation
            self._log_action(
                user=doctor,
                action='patient_folder_created',
                module=module,
                details={
                    'patient_id': patient_id,
                    'path': patient_path,
                    'folders': len(patient_folders)
                }
            )
            
            # Get doctor's workspace
            workspace = UserWorkspace.objects.get(user=doctor, module=module)
            
            # Create patient folder in database
            patient_folder, created = PatientFolder.objects.get_or_create(
                patient_id=patient_id,
                module=module,
                assigned_doctor=doctor,
                defaults={
                    's3_path': patient_path,
                    'created_by': doctor,
                    'encrypted_metadata_key': f"{patient_path}/patient_index.json",
                    'status': 'active'
                }
            )
            
            return {
                'success': True,
                'patient_id': patient_id,
                'patient_path': patient_path,
                'patient_folder_id': str(patient_folder.id),
                'folders_created': patient_folders,
                'message': f'Patient folder created successfully in {module}'
            }
            
        except Exception as e:
            logger.error(f"Failed to create patient folder: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def upload_patient_file(self, user: User, patient_id: str, file_data: bytes,
                          filename: str, file_type: str, module: str,
                          metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Upload file to patient's folder with encryption"""
        try:
            # Verify permissions
            if not self._check_patient_access(user, patient_id, module, 'write'):
                raise PermissionDenied("Insufficient permissions to upload file")
            
            # Generate secure file path
            file_path = self.generate_secure_path(
                module=module,
                user_type='doctor' if user.role == 'doctor' else user.role,
                user_id=str(self._get_doctor_id(user, patient_id, module)),
                patient_id=patient_id,
                file_type=file_type
            )
            
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            secure_filename = f"{uuid.uuid4()}.{file_extension}"
            full_path = f"{file_path}/{secure_filename}"
            
            # Encrypt file data
            encrypted_data = self.cipher.encrypt(file_data)
            
            # Prepare metadata
            file_metadata = {
                'original_filename': filename,
                'uploaded_by': str(user.id),
                'patient_id': patient_id,
                'module': module,
                'file_type': file_type,
                'upload_time': datetime.now().isoformat(),
                'checksum': hashlib.sha256(file_data).hexdigest(),
                'encrypted': 'true',
                'access_level': 'hipaa_protected'
            }
            
            if metadata:
                file_metadata.update(metadata)
            
            # Upload encrypted file
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=full_path,
                Body=encrypted_data,
                ServerSideEncryption='AES256',
                ContentType='application/octet-stream',
                Metadata=file_metadata
            )
            
            # Log file upload
            self._log_action(
                user=user,
                action='file_uploaded',
                module=module,
                details={
                    'patient_id': patient_id,
                    'filename': filename,
                    'file_type': file_type,
                    'file_size': len(file_data),
                    'path': full_path
                }
            )
            
            return {
                'success': True,
                'file_id': secure_filename,
                'file_path': full_path,
                'checksum': file_metadata['checksum'],
                'message': 'File uploaded successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def download_patient_file(self, user: User, patient_id: str, file_id: str,
                            module: str) -> Dict[str, Any]:
        """Download and decrypt patient file"""
        try:
            # Verify permissions
            if not self._check_patient_access(user, patient_id, module, 'read'):
                raise PermissionDenied("Insufficient permissions to access file")
            
            # Find file path
            file_path = self._find_patient_file(patient_id, file_id, module)
            if not file_path:
                return {'success': False, 'error': 'File not found'}
            
            # Download encrypted file
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            
            encrypted_data = response['Body'].read()
            metadata = response.get('Metadata', {})
            
            # Decrypt file data
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            # Verify checksum
            current_checksum = hashlib.sha256(decrypted_data).hexdigest()
            stored_checksum = metadata.get('checksum', '')
            
            if current_checksum != stored_checksum:
                raise ValueError("File integrity check failed")
            
            # Log file access
            self._log_action(
                user=user,
                action='file_accessed',
                module=module,
                details={
                    'patient_id': patient_id,
                    'file_id': file_id,
                    'file_path': file_path
                }
            )
            
            return {
                'success': True,
                'file_data': decrypted_data,
                'metadata': metadata,
                'original_filename': metadata.get('original_filename', file_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def list_patient_files(self, user: User, patient_id: str, module: str,
                         file_type: str = None) -> Dict[str, Any]:
        """List files in patient's folder"""
        try:
            # Verify permissions
            if not self._check_patient_access(user, patient_id, module, 'read'):
                raise PermissionDenied("Insufficient permissions to list files")
            
            # Get patient folder path
            patient_path = self.generate_secure_path(
                module=module,
                user_type='doctor' if user.role == 'doctor' else user.role,
                user_id=str(self._get_doctor_id(user, patient_id, module)),
                patient_id=patient_id,
                file_type=file_type or ''
            )
            
            # List objects in patient folder
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=patient_path
            )
            
            files = []
            for obj in response.get('Contents', []):
                if obj['Key'].endswith('.keep'):
                    continue
                    
                # Get metadata
                metadata_response = self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=obj['Key']
                )
                
                metadata = metadata_response.get('Metadata', {})
                
                files.append({
                    'file_id': obj['Key'].split('/')[-1],
                    'original_filename': metadata.get('original_filename', 'Unknown'),
                    'file_type': metadata.get('file_type', 'general'),
                    'upload_time': metadata.get('upload_time'),
                    'uploaded_by': metadata.get('uploaded_by'),
                    'size': obj['Size'],
                    'path': obj['Key']
                })
            
            return {
                'success': True,
                'files': files,
                'total_files': len(files),
                'patient_id': patient_id
            }
            
        except Exception as e:
            logger.error(f"Failed to list patient files: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _encrypt_patient_data(self, data: Dict[str, Any]) -> str:
        """Encrypt sensitive patient data"""
        try:
            json_data = json.dumps(data).encode()
            encrypted_data = self.cipher.encrypt(json_data)
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt patient data: {str(e)}")
            return ""

    def _check_patient_access(self, user: User, patient_id: str, module: str,
                            permission: str) -> bool:
        """Check if user has permission to access patient data"""
        try:
            # Super admin has all permissions
            if user.role == 'super_admin':
                return True
            
            # Admin has module-specific permissions
            if user.role == 'admin':
                # Check if admin has access to this module
                return self._check_admin_module_access(user, module)
            
            # Doctor can access their own patients
            if user.role == 'doctor':
                return self._check_doctor_patient_access(user, patient_id, module)
            
            # Patient can only access their own data
            if user.role == 'patient':
                return str(user.id) == patient_id
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check patient access: {str(e)}")
            return False

    def _check_admin_module_access(self, admin_user: User, module: str) -> bool:
        """Check if admin has access to specific module"""
        # This would integrate with your admin permissions system
        # For now, return True for all admins
        return True

    def _check_doctor_patient_access(self, doctor: User, patient_id: str, module: str) -> bool:
        """Check if doctor has access to specific patient"""
        # This would check against patient-doctor assignments
        # For now, implement basic logic
        try:
            # Check if patient folder exists under doctor's workspace
            patient_path = self.generate_secure_path(
                module=module,
                user_type='doctor',
                user_id=str(doctor.id),
                patient_id=patient_id
            )
            
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=f"{patient_path}/patient_index.json"
            )
            
            return True
            
        except:
            return False

    def _get_doctor_id(self, user: User, patient_id: str, module: str) -> str:
        """Get the doctor ID responsible for this patient"""
        if user.role == 'doctor':
            return str(user.id)
        
        # For admin/super_admin, find the primary doctor
        # This would integrate with your patient-doctor assignment system
        return str(user.id)  # Fallback to current user

    def _find_patient_file(self, patient_id: str, file_id: str, module: str) -> Optional[str]:
        """Find the full path of a patient file"""
        try:
            # Search across possible doctor folders
            # This is a simplified version - in production, you'd have an index
            prefix = f"{self.module_folders[module]}/staff/doctors/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            for obj in response.get('Contents', []):
                if file_id in obj['Key'] and patient_id in obj['Key']:
                    return obj['Key']
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find patient file: {str(e)}")
            return None

    def _generate_patient_permissions(self, doctor: User, patient_id: str) -> Dict[str, Any]:
        """Generate patient access permissions"""
        return {
            'doctor_id': str(doctor.id),
            'patient_id': patient_id,
            'permissions': {
                'read': True,
                'write': True,
                'delete': doctor.role in ['doctor', 'admin', 'super_admin']
            },
            'created_at': datetime.now().isoformat()
        }

    def _log_action(self, user: User, action: str, module: str, details: Dict[str, Any]):
        """Log user actions for audit trail"""
        try:
            log_entry = {
                'user_id': str(user.id),
                'user_role': user.role,
                'action': action,
                'module': module,
                'timestamp': datetime.now().isoformat(),
                'details': details,
                'ip_address': getattr(user, '_request_ip', 'unknown')
            }
            
            # Store audit log in S3
            log_path = f"audit_logs/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}.json"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=log_path,
                Body=json.dumps(log_entry).encode(),
                ServerSideEncryption='AES256',
                ContentType='application/json'
            )
            
        except Exception as e:
            logger.error(f"Failed to log action: {str(e)}")

# Global instance
secure_s3_manager = SecureS3Manager()
