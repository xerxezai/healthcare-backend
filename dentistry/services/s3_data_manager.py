"""
Dentistry S3 Data Management Service
Comprehensive S3 integration for dental data management with cloud storage capabilities
"""

import boto3
import logging
import json
import os
from datetime import datetime, timedelta
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.cache import cache
from botocore.exceptions import NoCredentialsError, ClientError
from ..models import DentistryInstitution, DentistryPatient, DentistryFile, DentistryAnalysis

logger = logging.getLogger(__name__)

class DentistryS3DataManager:
    """
    Comprehensive S3 data management service for dentistry module
    Handles file upload, storage, retrieval, and organization with dental-specific optimizations
    """
    
    def __init__(self):
        """Initialize S3 client with dentistry-specific configuration"""
        self.bucket_name = getattr(settings, 'DENTISTRY_S3_BUCKET', 'dentistry-data-storage')
        self.region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
                region_name=self.region
            )
            self.s3_resource = boto3.resource(
                's3',
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
                region_name=self.region
            )
            logger.info("Dentistry S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client for dentistry: {e}")
            self.s3_client = None
            self.s3_resource = None

    def upload_dental_file(self, file_obj, institution_id=None, patient_id=None, 
                          file_type='general', metadata=None):
        """
        Upload dental file to S3 with organized folder structure
        
        Args:
            file_obj: File object to upload
            institution_id: ID of the dental institution
            patient_id: ID of the patient (if applicable)
            file_type: Type of dental file (xray, photo, impression, etc.)
            metadata: Additional file metadata
            
        Returns:
            dict: Upload result with S3 URL and metadata
        """
        if not self.s3_client:
            raise Exception("S3 client not initialized")
            
        try:
            # Generate organized S3 key
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if patient_id:
                s3_key = f"patients/{patient_id}/{file_type}/{timestamp}_{file_obj.name}"
            elif institution_id:
                s3_key = f"institutions/{institution_id}/{file_type}/{timestamp}_{file_obj.name}"
            else:
                s3_key = f"general/{file_type}/{timestamp}_{file_obj.name}"
            
            # Prepare metadata
            upload_metadata = {
                'ContentType': file_obj.content_type,
                'UploadedAt': datetime.now().isoformat(),
                'FileType': file_type,
                'Module': 'dentistry'
            }
            
            if metadata:
                upload_metadata.update(metadata)
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'Metadata': {k: str(v) for k, v in upload_metadata.items()},
                    'ContentType': file_obj.content_type
                }
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            # Save to database
            dental_file = DentistryFile.objects.create(
                name=file_obj.name,
                file_type=file_type,
                s3_key=s3_key,
                s3_url=s3_url,
                institution_id=institution_id,
                patient_id=patient_id,
                metadata=upload_metadata,
                size=file_obj.size
            )
            
            logger.info(f"Successfully uploaded dental file: {s3_key}")
            
            return {
                'success': True,
                'file_id': dental_file.id,
                's3_key': s3_key,
                's3_url': s3_url,
                'metadata': upload_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to upload dental file: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def download_dental_file(self, s3_key, download_path=None):
        """
        Download dental file from S3
        
        Args:
            s3_key: S3 key of the file
            download_path: Local path to save the file
            
        Returns:
            str: Local file path or None if failed
        """
        if not self.s3_client:
            raise Exception("S3 client not initialized")
            
        try:
            if not download_path:
                download_path = f"/tmp/{os.path.basename(s3_key)}"
            
            self.s3_client.download_file(self.bucket_name, s3_key, download_path)
            logger.info(f"Successfully downloaded dental file: {s3_key}")
            return download_path
            
        except Exception as e:
            logger.error(f"Failed to download dental file {s3_key}: {e}")
            return None

    def generate_presigned_url(self, s3_key, expiration=3600):
        """
        Generate presigned URL for secure file access
        
        Args:
            s3_key: S3 key of the file
            expiration: URL expiration time in seconds
            
        Returns:
            str: Presigned URL or None if failed
        """
        if not self.s3_client:
            return None
            
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            return None

    def list_dental_files(self, prefix="", limit=100):
        """
        List dental files in S3 with optional filtering
        
        Args:
            prefix: S3 key prefix for filtering
            limit: Maximum number of files to return
            
        Returns:
            list: List of file information dictionaries
        """
        if not self.s3_client:
            return []
            
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list dental files: {e}")
            return []

    def delete_dental_file(self, s3_key, file_id=None):
        """
        Delete dental file from S3 and database
        
        Args:
            s3_key: S3 key of the file to delete
            file_id: Database ID of the file record
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.s3_client:
            return False
            
        try:
            # Delete from S3
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            
            # Delete from database
            if file_id:
                DentistryFile.objects.filter(id=file_id).delete()
            else:
                DentistryFile.objects.filter(s3_key=s3_key).delete()
            
            logger.info(f"Successfully deleted dental file: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete dental file {s3_key}: {e}")
            return False

    def sync_files_with_database(self):
        """
        Synchronize S3 files with database records
        
        Returns:
            dict: Sync statistics
        """
        if not self.s3_client:
            return {'error': 'S3 client not initialized'}
            
        try:
            # Get all files from S3
            s3_files = self.list_dental_files()
            s3_keys = {f['key'] for f in s3_files}
            
            # Get all files from database
            db_files = DentistryFile.objects.all()
            db_keys = {f.s3_key for f in db_files}
            
            # Find missing files
            missing_in_db = s3_keys - db_keys
            missing_in_s3 = db_keys - s3_keys
            
            # Create database records for missing files
            created_count = 0
            for s3_key in missing_in_db:
                s3_file = next((f for f in s3_files if f['key'] == s3_key), None)
                if s3_file:
                    DentistryFile.objects.create(
                        name=os.path.basename(s3_key),
                        file_type='unknown',
                        s3_key=s3_key,
                        s3_url=s3_file['url'],
                        size=s3_file['size'],
                        metadata={'synced': True}
                    )
                    created_count += 1
            
            # Remove database records for missing S3 files
            deleted_count = DentistryFile.objects.filter(s3_key__in=missing_in_s3).count()
            DentistryFile.objects.filter(s3_key__in=missing_in_s3).delete()
            
            return {
                'success': True,
                'total_s3_files': len(s3_files),
                'total_db_files': len(db_files),
                'created_in_db': created_count,
                'deleted_from_db': deleted_count,
                'missing_in_s3': len(missing_in_s3)
            }
            
        except Exception as e:
            logger.error(f"Failed to sync dental files: {e}")
            return {'error': str(e)}

    def get_storage_analytics(self):
        """
        Get storage analytics for dental data
        
        Returns:
            dict: Storage analytics data
        """
        if not self.s3_client:
            return {'error': 'S3 client not initialized'}
            
        try:
            # Get file counts by type
            file_counts = {}
            dental_files = DentistryFile.objects.all()
            
            for file_obj in dental_files:
                file_type = file_obj.file_type
                file_counts[file_type] = file_counts.get(file_type, 0) + 1
            
            # Calculate total storage usage
            total_size = sum(f.size for f in dental_files if f.size)
            
            # Get recent upload statistics
            last_week = datetime.now() - timedelta(days=7)
            recent_uploads = dental_files.filter(created_at__gte=last_week).count()
            
            # Institution and patient statistics
            total_institutions = DentistryInstitution.objects.count()
            total_patients = DentistryPatient.objects.count()
            
            return {
                'success': True,
                'total_files': len(dental_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2) if total_size else 0,
                'file_counts_by_type': file_counts,
                'recent_uploads_last_week': recent_uploads,
                'total_institutions': total_institutions,
                'total_patients': total_patients,
                'bucket_name': self.bucket_name,
                'region': self.region
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage analytics: {e}")
            return {'error': str(e)}

    def cleanup_old_files(self, days_old=90):
        """
        Cleanup old dental files from S3 and database
        
        Args:
            days_old: Number of days to consider files as old
            
        Returns:
            dict: Cleanup statistics
        """
        if not self.s3_client:
            return {'error': 'S3 client not initialized'}
            
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            old_files = DentistryFile.objects.filter(created_at__lt=cutoff_date)
            
            deleted_count = 0
            for file_obj in old_files:
                if self.delete_dental_file(file_obj.s3_key, file_obj.id):
                    deleted_count += 1
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old dental files: {e}")
            return {'error': str(e)}

    def backup_data(self, backup_bucket=None):
        """
        Create backup of dental data
        
        Args:
            backup_bucket: S3 bucket for backup (optional)
            
        Returns:
            dict: Backup result
        """
        if not backup_bucket:
            backup_bucket = f"{self.bucket_name}-backup"
            
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_prefix = f"backup_{timestamp}/"
            
            # List all files in main bucket
            files = self.list_dental_files()
            copied_count = 0
            
            for file_info in files:
                source_key = file_info['key']
                backup_key = f"{backup_prefix}{source_key}"
                
                # Copy file to backup bucket
                copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
                self.s3_client.copy_object(
                    CopySource=copy_source,
                    Bucket=backup_bucket,
                    Key=backup_key
                )
                copied_count += 1
            
            return {
                'success': True,
                'backup_bucket': backup_bucket,
                'backup_prefix': backup_prefix,
                'copied_files': copied_count,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Failed to backup dental data: {e}")
            return {'error': str(e)}

    def get_file_metadata(self, s3_key):
        """
        Get metadata for a specific dental file
        
        Args:
            s3_key: S3 key of the file
            
        Returns:
            dict: File metadata
        """
        if not self.s3_client:
            return {'error': 'S3 client not initialized'}
            
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                'success': True,
                'key': s3_key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response['ContentType'],
                'metadata': response.get('Metadata', {}),
                'etag': response['ETag']
            }
            
        except Exception as e:
            logger.error(f"Failed to get metadata for {s3_key}: {e}")
            return {'error': str(e)}

# Initialize global instance
dentistry_s3_manager = DentistryS3DataManager()
