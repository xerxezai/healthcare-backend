import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth.models import User
import logging
import os
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import mimetypes
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)


class RadiologyS3DataManager:
    """
    Comprehensive S3 data management service for radiology department.
    Handles DICOM files, reports, AI analysis results, and patient data
    with hierarchical organization and security.
    """
    
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        
        # Base prefixes for organized data structure
        self.base_prefixes = {
            'radiology_root': 'radiology/',
            'institutions': 'radiology/institutions/',
            'shared_resources': 'radiology/shared_resources/',
            'system': 'radiology/system/',
        }
        
        # DICOM and medical file types
        self.medical_file_types = {
            'dicom': ['.dcm', '.dicom', '.DCM'],
            'images': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp'],
            'reports': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
            'ai_analysis': ['.json', '.xml', '.csv'],
            'video': ['.mp4', '.avi', '.mov', '.wmv'],
            'archives': ['.zip', '.rar', '.7z', '.tar.gz']
        }
        
        # Initialize encryption for sensitive data
        self.encryption_key = self._get_or_create_encryption_key()

    def _get_or_create_encryption_key(self):
        """Generate or retrieve encryption key for sensitive data."""
        # In production, store this securely (AWS KMS, HashiCorp Vault, etc.)
        key_setting = getattr(settings, 'RADIOLOGY_ENCRYPTION_KEY', None)
        if key_setting:
            return key_setting.encode()
        
        # Generate new key (store this securely in production)
        key = Fernet.generate_key()
        logger.warning("Generated new encryption key. Store this securely!")
        return key

    def _encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive patient data."""
        f = Fernet(self.encryption_key)
        return f.encrypt(data.encode()).decode()

    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive patient data."""
        f = Fernet(self.encryption_key)
        return f.decrypt(encrypted_data.encode()).decode()

    def get_institution_prefix(self, institution_id: str) -> str:
        """Get S3 prefix for institution data."""
        return f"{self.base_prefixes['institutions']}{institution_id}/"

    def get_patient_prefix(self, institution_id: str, patient_id: str) -> str:
        """Get S3 prefix for patient data."""
        return f"{self.get_institution_prefix(institution_id)}patients/{patient_id}/"

    def get_study_prefix(self, institution_id: str, patient_id: str, study_id: str) -> str:
        """Get S3 prefix for study data."""
        return f"{self.get_patient_prefix(institution_id, patient_id)}studies/{study_id}/"

    def get_doctor_prefix(self, institution_id: str, doctor_id: str) -> str:
        """Get S3 prefix for doctor workspace."""
        return f"{self.get_institution_prefix(institution_id)}doctors/{doctor_id}/"

    def create_patient_profile(self, institution_id: str, patient_data: Dict) -> Tuple[str, Optional[str]]:
        """
        Create a new patient profile with encrypted sensitive data.
        
        Args:
            institution_id: Institution identifier
            patient_data: Patient information dictionary
            
        Returns:
            Tuple of (patient_id, error_message)
        """
        try:
            patient_id = str(uuid.uuid4())
            patient_prefix = self.get_patient_prefix(institution_id, patient_id)
            
            # Separate sensitive and non-sensitive data
            sensitive_fields = ['ssn', 'dob', 'address', 'phone', 'email']
            public_data = {}
            sensitive_data = {}
            
            for key, value in patient_data.items():
                if key in sensitive_fields:
                    sensitive_data[key] = value
                else:
                    public_data[key] = value
            
            # Create patient profile structure
            profile_data = {
                'patient_id': patient_id,
                'institution_id': institution_id,
                'created_at': datetime.utcnow().isoformat(),
                'created_by': patient_data.get('created_by'),
                'public_data': public_data,
                'sensitive_data_encrypted': self._encrypt_sensitive_data(json.dumps(sensitive_data)),
                'status': 'active',
                'access_level': 'standard'
            }
            
            # Upload patient profile
            profile_key = f"{patient_prefix}profile/patient_profile.json"
            self._upload_json_data(profile_key, profile_data)
            
            # Create directory structure
            directories = [
                f"{patient_prefix}studies/",
                f"{patient_prefix}history/",
                f"{patient_prefix}notes/"
            ]
            
            for directory in directories:
                self._create_directory(directory)
            
            logger.info(f"Created patient profile: {patient_id} in institution: {institution_id}")
            return patient_id, None
            
        except Exception as e:
            logger.error(f"Error creating patient profile: {e}")
            return None, str(e)

    def create_study(self, institution_id: str, patient_id: str, study_data: Dict) -> Tuple[str, Optional[str]]:
        """
        Create a new imaging study for a patient.
        
        Args:
            institution_id: Institution identifier
            patient_id: Patient identifier
            study_data: Study information dictionary
            
        Returns:
            Tuple of (study_id, error_message)
        """
        try:
            study_id = str(uuid.uuid4())
            study_prefix = self.get_study_prefix(institution_id, patient_id, study_id)
            
            # Create study metadata
            study_metadata = {
                'study_id': study_id,
                'patient_id': patient_id,
                'institution_id': institution_id,
                'study_type': study_data.get('study_type'),
                'modality': study_data.get('modality'),  # CT, MRI, X-Ray, etc.
                'body_part': study_data.get('body_part'),
                'ordered_by': study_data.get('ordered_by'),
                'performed_by': study_data.get('performed_by'),
                'study_date': study_data.get('study_date'),
                'created_at': datetime.utcnow().isoformat(),
                'status': 'created',
                'priority': study_data.get('priority', 'routine'),
                'clinical_indication': study_data.get('clinical_indication'),
                'study_description': study_data.get('description')
            }
            
            # Upload study metadata
            metadata_key = f"{study_prefix}metadata/study_metadata.json"
            self._upload_json_data(metadata_key, study_metadata)
            
            # Create study directory structure
            directories = [
                f"{study_prefix}dicom/",
                f"{study_prefix}reports/",
                f"{study_prefix}ai_analysis/",
                f"{study_prefix}images/",
                f"{study_prefix}annotations/"
            ]
            
            for directory in directories:
                self._create_directory(directory)
            
            logger.info(f"Created study: {study_id} for patient: {patient_id}")
            return study_id, None
            
        except Exception as e:
            logger.error(f"Error creating study: {e}")
            return None, str(e)

    def upload_dicom_file(self, institution_id: str, patient_id: str, study_id: str, 
                         file_obj, filename: str, metadata: Dict = None) -> Tuple[str, Optional[str]]:
        """
        Upload DICOM file to patient study.
        
        Args:
            institution_id: Institution identifier
            patient_id: Patient identifier
            study_id: Study identifier
            file_obj: File object to upload
            filename: Original filename
            metadata: Optional DICOM metadata
            
        Returns:
            Tuple of (file_key, error_message)
        """
        try:
            study_prefix = self.get_study_prefix(institution_id, patient_id, study_id)
            
            # Generate unique filename
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_key = f"{study_prefix}dicom/{unique_filename}"
            
            # Upload file
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                file_key,
                ExtraArgs={
                    'ContentType': 'application/dicom',
                    'Metadata': {
                        'original-filename': filename,
                        'upload-timestamp': datetime.utcnow().isoformat(),
                        'patient-id': patient_id,
                        'study-id': study_id
                    }
                }
            )
            
            # Store DICOM metadata if provided
            if metadata:
                metadata_key = f"{study_prefix}metadata/dicom_{unique_filename}.json"
                self._upload_json_data(metadata_key, metadata)
            
            # Update study status
            self._update_study_status(institution_id, patient_id, study_id, 'images_uploaded')
            
            logger.info(f"Uploaded DICOM file: {filename} to study: {study_id}")
            return file_key, None
            
        except Exception as e:
            logger.error(f"Error uploading DICOM file: {e}")
            return None, str(e)

    def upload_report(self, institution_id: str, patient_id: str, study_id: str,
                     report_data: Dict, report_type: str = 'radiology') -> Tuple[str, Optional[str]]:
        """
        Upload radiology report to patient study.
        
        Args:
            institution_id: Institution identifier
            patient_id: Patient identifier
            study_id: Study identifier
            report_data: Report content and metadata
            report_type: Type of report (radiology, ai_analysis, etc.)
            
        Returns:
            Tuple of (report_key, error_message)
        """
        try:
            study_prefix = self.get_study_prefix(institution_id, patient_id, study_id)
            
            # Generate report metadata
            report_metadata = {
                'report_id': str(uuid.uuid4()),
                'study_id': study_id,
                'patient_id': patient_id,
                'report_type': report_type,
                'created_at': datetime.utcnow().isoformat(),
                'created_by': report_data.get('created_by'),
                'status': report_data.get('status', 'draft'),
                'findings': report_data.get('findings'),
                'impression': report_data.get('impression'),
                'recommendations': report_data.get('recommendations'),
                'ai_assisted': report_data.get('ai_assisted', False),
                'accuracy_score': report_data.get('accuracy_score'),
                'version': report_data.get('version', '1.0')
            }
            
            # Upload report
            report_key = f"{study_prefix}reports/{report_type}_report_{report_metadata['report_id']}.json"
            self._upload_json_data(report_key, report_metadata)
            
            # Update study status
            self._update_study_status(institution_id, patient_id, study_id, 'report_available')
            
            logger.info(f"Uploaded {report_type} report for study: {study_id}")
            return report_key, None
            
        except Exception as e:
            logger.error(f"Error uploading report: {e}")
            return None, str(e)

    def store_ai_analysis_result(self, institution_id: str, patient_id: str, study_id: str,
                               analysis_data: Dict, analysis_type: str) -> Tuple[str, Optional[str]]:
        """
        Store AI analysis results for a study.
        
        Args:
            institution_id: Institution identifier
            patient_id: Patient identifier
            study_id: Study identifier
            analysis_data: AI analysis results
            analysis_type: Type of AI analysis (rads_calculator, report_correction, etc.)
            
        Returns:
            Tuple of (analysis_key, error_message)
        """
        try:
            study_prefix = self.get_study_prefix(institution_id, patient_id, study_id)
            
            # Generate analysis metadata
            analysis_metadata = {
                'analysis_id': str(uuid.uuid4()),
                'study_id': study_id,
                'patient_id': patient_id,
                'analysis_type': analysis_type,
                'created_at': datetime.utcnow().isoformat(),
                'ai_model_version': analysis_data.get('model_version'),
                'confidence_score': analysis_data.get('confidence_score'),
                'processing_time': analysis_data.get('processing_time'),
                'results': analysis_data.get('results'),
                'recommendations': analysis_data.get('recommendations'),
                'flags': analysis_data.get('flags', []),
                'metadata': analysis_data.get('metadata', {})
            }
            
            # Upload analysis results
            analysis_key = f"{study_prefix}ai_analysis/{analysis_type}_{analysis_metadata['analysis_id']}.json"
            self._upload_json_data(analysis_key, analysis_metadata)
            
            logger.info(f"Stored {analysis_type} AI analysis for study: {study_id}")
            return analysis_key, None
            
        except Exception as e:
            logger.error(f"Error storing AI analysis: {e}")
            return None, str(e)

    def get_patient_studies(self, institution_id: str, patient_id: str, 
                          limit: int = 50) -> Tuple[List[Dict], Optional[str]]:
        """
        Retrieve all studies for a patient.
        
        Args:
            institution_id: Institution identifier
            patient_id: Patient identifier
            limit: Maximum number of studies to return
            
        Returns:
            Tuple of (studies_list, error_message)
        """
        try:
            patient_prefix = self.get_patient_prefix(institution_id, patient_id)
            studies_prefix = f"{patient_prefix}studies/"
            
            # List all study directories
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=studies_prefix,
                Delimiter='/'
            )
            
            studies = []
            for common_prefix in response.get('CommonPrefixes', []):
                study_id = common_prefix['Prefix'].split('/')[-2]
                
                # Get study metadata
                metadata_key = f"{common_prefix['Prefix']}metadata/study_metadata.json"
                study_metadata = self._get_json_data(metadata_key)
                
                if study_metadata:
                    studies.append(study_metadata)
                
                if len(studies) >= limit:
                    break
            
            # Sort by creation date (newest first)
            studies.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return studies, None
            
        except Exception as e:
            logger.error(f"Error retrieving patient studies: {e}")
            return [], str(e)

    def get_study_details(self, institution_id: str, patient_id: str, study_id: str) -> Tuple[Dict, Optional[str]]:
        """
        Get complete study details including files and reports.
        
        Args:
            institution_id: Institution identifier
            patient_id: Patient identifier
            study_id: Study identifier
            
        Returns:
            Tuple of (study_details, error_message)
        """
        try:
            study_prefix = self.get_study_prefix(institution_id, patient_id, study_id)
            
            # Get study metadata
            metadata_key = f"{study_prefix}metadata/study_metadata.json"
            study_metadata = self._get_json_data(metadata_key)
            
            if not study_metadata:
                return {}, "Study not found"
            
            # Get DICOM files
            dicom_files = self._list_files_in_prefix(f"{study_prefix}dicom/")
            
            # Get reports
            reports = self._list_files_in_prefix(f"{study_prefix}reports/")
            
            # Get AI analysis results
            ai_analyses = self._list_files_in_prefix(f"{study_prefix}ai_analysis/")
            
            # Get images
            images = self._list_files_in_prefix(f"{study_prefix}images/")
            
            study_details = {
                'metadata': study_metadata,
                'dicom_files': dicom_files,
                'reports': reports,
                'ai_analyses': ai_analyses,
                'images': images,
                'total_files': len(dicom_files) + len(reports) + len(ai_analyses) + len(images)
            }
            
            return study_details, None
            
        except Exception as e:
            logger.error(f"Error retrieving study details: {e}")
            return {}, str(e)

    def search_studies(self, institution_id: str, search_criteria: Dict, 
                      limit: int = 100) -> Tuple[List[Dict], Optional[str]]:
        """
        Search studies based on various criteria.
        
        Args:
            institution_id: Institution identifier
            search_criteria: Search parameters
            limit: Maximum number of results
            
        Returns:
            Tuple of (matching_studies, error_message)
        """
        try:
            institution_prefix = self.get_institution_prefix(institution_id)
            patients_prefix = f"{institution_prefix}patients/"
            
            # This is a simplified search. In production, consider using
            # AWS CloudSearch, Elasticsearch, or database indexing
            matching_studies = []
            
            # List all patients
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=patients_prefix,
                Delimiter='/'
            )
            
            for patient_prefix in response.get('CommonPrefixes', []):
                patient_id = patient_prefix['Prefix'].split('/')[-2]
                
                # Get patient studies
                studies, error = self.get_patient_studies(institution_id, patient_id, limit)
                
                if error:
                    continue
                
                # Filter studies based on search criteria
                for study in studies:
                    if self._matches_search_criteria(study, search_criteria):
                        study['patient_id'] = patient_id
                        matching_studies.append(study)
                
                if len(matching_studies) >= limit:
                    break
            
            return matching_studies[:limit], None
            
        except Exception as e:
            logger.error(f"Error searching studies: {e}")
            return [], str(e)

    def _matches_search_criteria(self, study: Dict, criteria: Dict) -> bool:
        """Check if study matches search criteria."""
        for key, value in criteria.items():
            if key in study:
                if isinstance(value, str) and value.lower() not in str(study[key]).lower():
                    return False
                elif not isinstance(value, str) and study[key] != value:
                    return False
        return True

    def _upload_json_data(self, key: str, data: Dict):
        """Upload JSON data to S3."""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )

    def _get_json_data(self, key: str) -> Optional[Dict]:
        """Retrieve and parse JSON data from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError:
            return None

    def _create_directory(self, prefix: str):
        """Create directory structure in S3."""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=f"{prefix}.keep",
            Body=b'',
            ContentType='text/plain'
        )

    def _list_files_in_prefix(self, prefix: str) -> List[Dict]:
        """List all files in a specific prefix."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                if not obj['Key'].endswith('.keep'):
                    files.append({
                        'key': obj['Key'],
                        'filename': obj['Key'].split('/')[-1],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'url': self._generate_presigned_url(obj['Key'])
                    })
            
            return files
        except ClientError:
            return []

    def _generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for file access."""
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expires_in
            )
        except ClientError:
            return ""

    def _update_study_status(self, institution_id: str, patient_id: str, study_id: str, status: str):
        """Update study status."""
        try:
            study_prefix = self.get_study_prefix(institution_id, patient_id, study_id)
            metadata_key = f"{study_prefix}metadata/study_metadata.json"
            
            study_metadata = self._get_json_data(metadata_key)
            if study_metadata:
                study_metadata['status'] = status
                study_metadata['updated_at'] = datetime.utcnow().isoformat()
                self._upload_json_data(metadata_key, study_metadata)
                
        except Exception as e:
            logger.error(f"Error updating study status: {e}")

    def create_doctor_workspace(self, institution_id: str, doctor_id: str, doctor_data: Dict) -> Tuple[str, Optional[str]]:
        """Create doctor workspace with templates and preferences."""
        try:
            doctor_prefix = self.get_doctor_prefix(institution_id, doctor_id)
            
            workspace_data = {
                'doctor_id': doctor_id,
                'institution_id': institution_id,
                'created_at': datetime.utcnow().isoformat(),
                'preferences': doctor_data.get('preferences', {}),
                'specializations': doctor_data.get('specializations', []),
                'report_templates': doctor_data.get('templates', [])
            }
            
            # Create workspace structure
            workspace_key = f"{doctor_prefix}workspace/doctor_profile.json"
            self._upload_json_data(workspace_key, workspace_data)
            
            # Create directory structure
            directories = [
                f"{doctor_prefix}templates/",
                f"{doctor_prefix}preferences/",
                f"{doctor_prefix}drafts/"
            ]
            
            for directory in directories:
                self._create_directory(directory)
            
            return doctor_prefix, None
            
        except Exception as e:
            logger.error(f"Error creating doctor workspace: {e}")
            return None, str(e)

    def get_analytics_data(self, institution_id: str, date_range: Dict = None) -> Tuple[Dict, Optional[str]]:
        """Get analytics data for the institution."""
        try:
            institution_prefix = self.get_institution_prefix(institution_id)
            
            # This is a simplified analytics implementation
            # In production, consider using AWS Analytics services
            analytics = {
                'total_patients': 0,
                'total_studies': 0,
                'studies_by_modality': {},
                'reports_generated': 0,
                'ai_analyses_performed': 0,
                'storage_usage': 0
            }
            
            # Get basic counts (simplified)
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=institution_prefix
            )
            
            total_size = 0
            for obj in response.get('Contents', []):
                total_size += obj['Size']
                
                # Count different types of files
                if '/studies/' in obj['Key']:
                    if '/dicom/' in obj['Key']:
                        analytics['total_studies'] += 1
                    elif '/reports/' in obj['Key']:
                        analytics['reports_generated'] += 1
                    elif '/ai_analysis/' in obj['Key']:
                        analytics['ai_analyses_performed'] += 1
            
            analytics['storage_usage'] = total_size
            
            return analytics, None
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            return {}, str(e)


# Initialize service instance
radiology_s3_manager = RadiologyS3DataManager()
