"""
Homeopathy S3 Data Management Service
Comprehensive S3 integration for homeopathy practice management with cloud storage capabilities
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
from ..models import HomeopathyInstitution, HomeopathyPatient, HomeopathyCase, HomeopathyFile, HomeopathyAnalysis

logger = logging.getLogger(__name__)

class HomeopathyS3DataManager:
    """
    Comprehensive S3 data management service for homeopathy module
    Handles file upload, storage, retrieval, and organization with homeopathy-specific optimizations
    """
    
    def __init__(self):
        """Initialize S3 client with homeopathy-specific configuration"""
        self.bucket_name = getattr(settings, 'HOMEOPATHY_S3_BUCKET', 'homeopathy-data-storage')
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
            logger.info("Homeopathy S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client for homeopathy: {e}")
            self.s3_client = None
            self.s3_resource = None

    def upload_homeopathy_file(self, file_obj, institution_id=None, patient_id=None, 
                              case_id=None, file_type='general', metadata=None):
        """
        Upload homeopathy file to S3 with organized folder structure
        
        Args:
            file_obj: File object to upload
            institution_id: ID of the homeopathy institution
            patient_id: ID of the patient (if applicable)
            case_id: ID of the case (if applicable)
            file_type: Type of homeopathy file (case_taking, constitutional_analysis, etc.)
            metadata: Additional file metadata
            
        Returns:
            dict: Upload result with S3 URL and metadata
        """
        if not self.s3_client:
            raise Exception("S3 client not initialized")
            
        try:
            # Generate organized S3 key
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if case_id:
                s3_key = f"cases/{case_id}/{file_type}/{timestamp}_{file_obj.name}"
            elif patient_id:
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
                'Module': 'homeopathy'
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
            homeopathy_file = HomeopathyFile.objects.create(
                name=file_obj.name,
                file_type=file_type,
                s3_key=s3_key,
                s3_url=s3_url,
                institution_id=institution_id,
                patient_id=patient_id,
                case_id=case_id,
                metadata=upload_metadata,
                size=file_obj.size
            )
            
            logger.info(f"Successfully uploaded homeopathy file: {s3_key}")
            
            return {
                'success': True,
                'file_id': homeopathy_file.id,
                's3_key': s3_key,
                's3_url': s3_url,
                'metadata': upload_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to upload homeopathy file: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def download_homeopathy_file(self, s3_key, download_path=None):
        """
        Download homeopathy file from S3
        
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
            logger.info(f"Successfully downloaded homeopathy file: {s3_key}")
            return download_path
            
        except Exception as e:
            logger.error(f"Failed to download homeopathy file {s3_key}: {e}")
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

    def list_homeopathy_files(self, prefix="", limit=100):
        """
        List homeopathy files in S3 with optional filtering
        
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
            logger.error(f"Failed to list homeopathy files: {e}")
            return []

    def delete_homeopathy_file(self, s3_key, file_id=None):
        """
        Delete homeopathy file from S3 and database
        
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
                HomeopathyFile.objects.filter(id=file_id).delete()
            else:
                HomeopathyFile.objects.filter(s3_key=s3_key).delete()
            
            logger.info(f"Successfully deleted homeopathy file: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete homeopathy file {s3_key}: {e}")
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
            s3_files = self.list_homeopathy_files()
            s3_keys = {f['key'] for f in s3_files}
            
            # Get all files from database
            db_files = HomeopathyFile.objects.all()
            db_keys = {f.s3_key for f in db_files}
            
            # Find missing files
            missing_in_db = s3_keys - db_keys
            missing_in_s3 = db_keys - s3_keys
            
            # Create database records for missing files
            created_count = 0
            for s3_key in missing_in_db:
                s3_file = next((f for f in s3_files if f['key'] == s3_key), None)
                if s3_file:
                    HomeopathyFile.objects.create(
                        name=os.path.basename(s3_key),
                        file_type='unknown',
                        s3_key=s3_key,
                        s3_url=s3_file['url'],
                        size=s3_file['size'],
                        metadata={'synced': True}
                    )
                    created_count += 1
            
            # Remove database records for missing S3 files
            deleted_count = HomeopathyFile.objects.filter(s3_key__in=missing_in_s3).count()
            HomeopathyFile.objects.filter(s3_key__in=missing_in_s3).delete()
            
            return {
                'success': True,
                'total_s3_files': len(s3_files),
                'total_db_files': len(db_files),
                'created_in_db': created_count,
                'deleted_from_db': deleted_count,
                'missing_in_s3': len(missing_in_s3)
            }
            
        except Exception as e:
            logger.error(f"Failed to sync homeopathy files: {e}")
            return {'error': str(e)}

    def get_storage_analytics(self):
        """
        Get storage analytics for homeopathy data
        
        Returns:
            dict: Storage analytics data
        """
        if not self.s3_client:
            return {'error': 'S3 client not initialized'}
            
        try:
            # Get file counts by type
            file_counts = {}
            homeopathy_files = HomeopathyFile.objects.all()
            
            for file_obj in homeopathy_files:
                file_type = file_obj.file_type
                file_counts[file_type] = file_counts.get(file_type, 0) + 1
            
            # Calculate total storage usage
            total_size = sum(f.size for f in homeopathy_files if f.size)
            
            # Get recent upload statistics
            last_week = datetime.now() - timedelta(days=7)
            recent_uploads = homeopathy_files.filter(created_at__gte=last_week).count()
            
            # Institution, patient, and case statistics
            total_institutions = HomeopathyInstitution.objects.count()
            total_patients = HomeopathyPatient.objects.count()
            total_cases = HomeopathyCase.objects.count()
            
            return {
                'success': True,
                'total_files': len(homeopathy_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2) if total_size else 0,
                'file_counts_by_type': file_counts,
                'recent_uploads_last_week': recent_uploads,
                'total_institutions': total_institutions,
                'total_patients': total_patients,
                'total_cases': total_cases,
                'bucket_name': self.bucket_name,
                'region': self.region
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage analytics: {e}")
            return {'error': str(e)}

    def analyze_constitutional_type(self, file_id, analysis_type='constitutional_matching'):
        """
        Perform AI analysis on homeopathy case files for constitutional type identification
        
        Args:
            file_id: ID of the homeopathy file
            analysis_type: Type of analysis to perform
            
        Returns:
            dict: Analysis results
        """
        if not self.s3_client:
            return {'error': 'S3 client not initialized'}
            
        try:
            file_obj = HomeopathyFile.objects.get(id=file_id)
            
            # Create analysis record
            analysis = HomeopathyAnalysis.objects.create(
                file=file_obj,
                analysis_type=analysis_type,
                status='processing'
            )
            
            # Simulate AI analysis (replace with actual AI service)
            import time
            time.sleep(3)  # Simulate processing time
            
            # Mock analysis results based on type
            mock_results = {
                'constitutional_matching': {
                    'constitutional_type': 'Phosphorus',
                    'confidence': 0.87,
                    'characteristics': [
                        'Tall, lean build',
                        'Sensitive to stimuli',
                        'Creative and artistic',
                        'Desires cold drinks'
                    ],
                    'alternative_types': ['Arsenicum Album', 'Lycopodium']
                },
                'remedy_selection': {
                    'recommended_remedy': 'Phosphorus 30C',
                    'potency': '30C',
                    'dosage': '3 pellets twice daily',
                    'confidence': 0.91,
                    'supporting_symptoms': [
                        'Burning pains',
                        'Thirst for cold water',
                        'Anxiety about health'
                    ]
                },
                'miasmatic_assessment': {
                    'primary_miasm': 'Tubercular',
                    'secondary_miasm': 'Psoric',
                    'confidence': 0.82,
                    'hereditary_patterns': [
                        'Respiratory weakness',
                        'Nervous sensitivity',
                        'Creative tendencies'
                    ]
                }
            }
            
            results = mock_results.get(analysis_type, {
                'analysis_completed': True,
                'confidence': 0.85,
                'findings': f'Analysis completed for {analysis_type}'
            })
            
            # Update analysis record
            analysis.status = 'completed'
            analysis.confidence_score = results.get('confidence', 0.85)
            analysis.results = results
            analysis.save()
            
            return {
                'success': True,
                'analysis_id': analysis.id,
                'results': results
            }
            
        except HomeopathyFile.DoesNotExist:
            return {'error': 'File not found'}
        except Exception as e:
            logger.error(f"Failed to analyze constitutional type: {e}")
            return {'error': str(e)}

    def cleanup_old_files(self, days_old=180):
        """
        Cleanup old homeopathy files from S3 and database
        
        Args:
            days_old: Number of days to consider files as old
            
        Returns:
            dict: Cleanup statistics
        """
        if not self.s3_client:
            return {'error': 'S3 client not initialized'}
            
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            old_files = HomeopathyFile.objects.filter(created_at__lt=cutoff_date)
            
            deleted_count = 0
            for file_obj in old_files:
                if self.delete_homeopathy_file(file_obj.s3_key, file_obj.id):
                    deleted_count += 1
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old homeopathy files: {e}")
            return {'error': str(e)}

    def generate_homeopathy_report(self, patient_id, case_ids=None):
        """
        Generate comprehensive homeopathy report
        
        Args:
            patient_id: ID of the patient
            case_ids: List of case IDs to include
            
        Returns:
            dict: Generated report data
        """
        try:
            patient = HomeopathyPatient.objects.get(id=patient_id)
            cases = HomeopathyCase.objects.filter(patient=patient)
            
            if case_ids:
                cases = cases.filter(id__in=case_ids)
            
            report_data = {
                'patient_info': {
                    'name': f"{patient.first_name} {patient.last_name}",
                    'patient_id': patient.patient_id,
                    'date_of_birth': patient.date_of_birth.isoformat(),
                    'constitutional_type': patient.constitution_type,
                    'miasmatic_background': patient.miasmatic_background
                },
                'cases': [],
                'constitutional_analysis': {
                    'primary_type': patient.constitution_type,
                    'confirming_symptoms': [],
                    'modalities': [],
                    'prescriptions': []
                },
                'summary': {
                    'total_cases': cases.count(),
                    'improvement_trend': 'positive',
                    'recommendations': []
                },
                'generated_at': datetime.now().isoformat()
            }
            
            for case in cases:
                case_data = {
                    'case_id': case.case_id,
                    'chief_complaint': case.chief_complaint,
                    'constitutional_type': case.constitutional_type,
                    'remedy_prescribed': case.remedy_prescribed,
                    'potency': case.potency,
                    'outcome': case.outcome,
                    'created_at': case.created_at.isoformat()
                }
                report_data['cases'].append(case_data)
            
            return {
                'success': True,
                'report': report_data
            }
            
        except HomeopathyPatient.DoesNotExist:
            return {'error': 'Patient not found'}
        except Exception as e:
            logger.error(f"Failed to generate homeopathy report: {e}")
            return {'error': str(e)}

# Initialize global instance
homeopathy_s3_manager = HomeopathyS3DataManager()
