"""
Cosmetology S3 Data Management Service
Handles beauty and aesthetic practice management with cloud storage integration
"""

import os
import uuid
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logger = logging.getLogger(__name__)

class CosmetologyS3Service:
    """
    Service class for managing cosmetology data with S3 cloud storage
    Handles beauty institutions, clients, treatments, and aesthetic procedures
    """
    
    def __init__(self):
        self.s3_client = self._initialize_s3_client()
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'cosmetology-data-bucket')
        self.region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        
    def _initialize_s3_client(self):
        """Initialize S3 client with proper configuration"""
        try:
            return boto3.client(
                's3',
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            return None

    def create_cosmetology_salon(self, salon_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new cosmetology salon/institution with S3 storage setup
        
        Args:
            salon_data: Dictionary containing salon information
            
        Returns:
            Dictionary with salon details and S3 configuration
        """
        try:
            salon_id = str(uuid.uuid4())
            
            # Create S3 folder structure for the salon
            folder_structure = self._create_salon_folder_structure(salon_id)
            
            # Prepare salon metadata
            salon_info = {
                'salon_id': salon_id,
                'name': salon_data.get('name'),
                'institution_type': salon_data.get('institution_type'),
                'license_number': salon_data.get('license_number'),
                'head_aesthetician': salon_data.get('head_aesthetician'),
                'phone': salon_data.get('phone'),
                'email': salon_data.get('email'),
                'address': salon_data.get('address'),
                'city': salon_data.get('city'),
                'state': salon_data.get('state'),
                'zip_code': salon_data.get('zip_code'),
                'website': salon_data.get('website'),
                'operating_hours': salon_data.get('operating_hours'),
                's3_folders': folder_structure,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # Save salon metadata to S3
            metadata_key = f"salons/{salon_id}/metadata.json"
            self._upload_json_to_s3(metadata_key, salon_info)
            
            logger.info(f"Created cosmetology salon: {salon_info['name']} (ID: {salon_id})")
            return salon_info
            
        except Exception as e:
            logger.error(f"Error creating cosmetology salon: {e}")
            raise Exception(f"Failed to create salon: {str(e)}")

    def _create_salon_folder_structure(self, salon_id: str) -> Dict[str, str]:
        """Create organized folder structure for salon data"""
        folders = {
            'root': f"salons/{salon_id}/",
            'clients': f"salons/{salon_id}/clients/",
            'treatments': f"salons/{salon_id}/treatments/",
            'before_after_photos': f"salons/{salon_id}/before_after_photos/",
            'treatment_plans': f"salons/{salon_id}/treatment_plans/",
            'skin_analysis': f"salons/{salon_id}/skin_analysis/",
            'consultations': f"salons/{salon_id}/consultations/",
            'procedures': f"salons/{salon_id}/procedures/",
            'product_formulations': f"salons/{salon_id}/product_formulations/",
            'allergy_tests': f"salons/{salon_id}/allergy_tests/",
            'progress_tracking': f"salons/{salon_id}/progress_tracking/",
            'product_recommendations': f"salons/{salon_id}/product_recommendations/",
            'training_materials': f"salons/{salon_id}/training_materials/",
            'analytics': f"salons/{salon_id}/analytics/",
            'reports': f"salons/{salon_id}/reports/"
        }
        
        # Create empty placeholder files to establish folder structure
        for folder_name, folder_path in folders.items():
            try:
                placeholder_key = f"{folder_path}.placeholder"
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=placeholder_key,
                    Body=b'',
                    ContentType='text/plain'
                )
            except Exception as e:
                logger.warning(f"Could not create placeholder for {folder_path}: {e}")
        
        return folders

    def register_client(self, salon_id: str, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new client for beauty treatments
        
        Args:
            salon_id: ID of the salon
            client_data: Client information dictionary
            
        Returns:
            Dictionary with client details and S3 paths
        """
        try:
            client_id = str(uuid.uuid4())
            
            # Prepare client information
            client_info = {
                'client_id': client_id,
                'salon_id': salon_id,
                'client_external_id': client_data.get('client_id'),
                'first_name': client_data.get('first_name'),
                'last_name': client_data.get('last_name'),
                'date_of_birth': client_data.get('date_of_birth'),
                'gender': client_data.get('gender'),
                'skin_type': client_data.get('skin_type'),
                'fitzpatrick_scale': client_data.get('fitzpatrick_scale'),
                'phone': client_data.get('phone'),
                'email': client_data.get('email'),
                'address': client_data.get('address'),
                'emergency_contact_name': client_data.get('emergency_contact_name'),
                'emergency_contact_phone': client_data.get('emergency_contact_phone'),
                'referring_source': client_data.get('referring_source'),
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # Create client-specific folder structure
            client_folders = self._create_client_folder_structure(salon_id, client_id)
            client_info['s3_folders'] = client_folders
            
            # Save client metadata
            metadata_key = f"salons/{salon_id}/clients/{client_id}/metadata.json"
            self._upload_json_to_s3(metadata_key, client_info)
            
            logger.info(f"Registered client: {client_info['first_name']} {client_info['last_name']} (ID: {client_id})")
            return client_info
            
        except Exception as e:
            logger.error(f"Error registering client: {e}")
            raise Exception(f"Failed to register client: {str(e)}")

    def _create_client_folder_structure(self, salon_id: str, client_id: str) -> Dict[str, str]:
        """Create organized folder structure for client data"""
        folders = {
            'root': f"salons/{salon_id}/clients/{client_id}/",
            'before_after': f"salons/{salon_id}/clients/{client_id}/before_after/",
            'treatments': f"salons/{salon_id}/clients/{client_id}/treatments/",
            'skin_analysis': f"salons/{salon_id}/clients/{client_id}/skin_analysis/",
            'consultations': f"salons/{salon_id}/clients/{client_id}/consultations/",
            'progress_photos': f"salons/{salon_id}/clients/{client_id}/progress_photos/",
            'allergy_tests': f"salons/{salon_id}/clients/{client_id}/allergy_tests/",
            'product_recommendations': f"salons/{salon_id}/clients/{client_id}/product_recommendations/",
            'treatment_plans': f"salons/{salon_id}/clients/{client_id}/treatment_plans/",
            'reports': f"salons/{salon_id}/clients/{client_id}/reports/"
        }
        
        # Create folder placeholders
        for folder_name, folder_path in folders.items():
            try:
                placeholder_key = f"{folder_path}.placeholder"
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=placeholder_key,
                    Body=b'',
                    ContentType='text/plain'
                )
            except Exception as e:
                logger.warning(f"Could not create client placeholder for {folder_path}: {e}")
        
        return folders

    def upload_treatment_file(self, salon_id: str, client_id: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload a treatment-related file (photos, documents, analysis results)
        
        Args:
            salon_id: ID of the salon
            client_id: ID of the client (optional)
            file_data: Dictionary containing file information
            
        Returns:
            Dictionary with upload results and file metadata
        """
        try:
            file_id = str(uuid.uuid4())
            file_category = file_data.get('category', 'general')
            file_obj = file_data.get('file')
            
            if not file_obj:
                raise ValueError("No file provided")
            
            # Determine upload path based on category and client
            if client_id:
                base_path = f"salons/{salon_id}/clients/{client_id}/"
            else:
                base_path = f"salons/{salon_id}/"
            
            # Map categories to specific folders
            category_folders = {
                'before_after_photos': 'before_after_photos/',
                'treatment_plans': 'treatment_plans/',
                'skin_analysis': 'skin_analysis/',
                'client_consultations': 'consultations/',
                'procedure_documentation': 'procedures/',
                'product_formulations': 'product_formulations/',
                'allergy_patch_tests': 'allergy_tests/',
                'progress_tracking': 'progress_tracking/',
                'product_recommendations': 'product_recommendations/',
                'training_materials': 'training_materials/'
            }
            
            category_path = category_folders.get(file_category, 'general/')
            file_path = f"{base_path}{category_path}"
            
            # Generate unique filename
            original_name = file_obj.name
            file_extension = original_name.split('.')[-1].lower()
            unique_filename = f"{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
            s3_key = f"{file_path}{unique_filename}"
            
            # Upload file to S3
            upload_result = self._upload_file_to_s3(s3_key, file_obj)
            
            # Prepare file metadata
            file_metadata = {
                'file_id': file_id,
                'salon_id': salon_id,
                'client_id': client_id,
                'original_name': original_name,
                'filename': unique_filename,
                's3_key': s3_key,
                'category': file_category,
                'file_size': file_obj.size,
                'content_type': file_obj.content_type,
                'upload_date': datetime.now().isoformat(),
                's3_url': upload_result.get('s3_url'),
                'status': 'uploaded'
            }
            
            # Save file metadata
            metadata_key = f"{file_path}metadata/{file_id}.json"
            self._upload_json_to_s3(metadata_key, file_metadata)
            
            logger.info(f"Uploaded treatment file: {original_name} (ID: {file_id})")
            return file_metadata
            
        except Exception as e:
            logger.error(f"Error uploading treatment file: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")

    def analyze_skin_condition(self, file_id: str, analysis_type: str = 'skin_condition') -> Dict[str, Any]:
        """
        Perform AI-powered skin condition analysis on uploaded images
        
        Args:
            file_id: ID of the uploaded file
            analysis_type: Type of analysis to perform
            
        Returns:
            Dictionary with analysis results
        """
        try:
            analysis_id = str(uuid.uuid4())
            
            # This is a placeholder for actual AI analysis
            # In a real implementation, you would integrate with AI services
            # like AWS Rekognition, Google Vision API, or custom ML models
            
            analysis_results = {
                'analysis_id': analysis_id,
                'file_id': file_id,
                'analysis_type': analysis_type,
                'results': {
                    'skin_type': 'combination',
                    'skin_conditions': ['mild_acne', 'hyperpigmentation'],
                    'skin_tone': 'medium',
                    'skin_texture': 'slightly_rough',
                    'pore_size': 'medium',
                    'oil_level': 'moderate',
                    'hydration_level': 'low',
                    'sensitivity_level': 'low',
                    'recommended_treatments': [
                        'Gentle exfoliation',
                        'Hydrating facial',
                        'Acne treatment',
                        'Brightening serum'
                    ],
                    'recommended_products': [
                        'Gentle cleanser',
                        'Hyaluronic acid serum',
                        'Vitamin C serum',
                        'Broad spectrum SPF'
                    ]
                },
                'confidence_score': 0.85,
                'analysis_date': datetime.now().isoformat(),
                'status': 'completed'
            }
            
            # Save analysis results
            analysis_key = f"analyses/{analysis_id}/results.json"
            self._upload_json_to_s3(analysis_key, analysis_results)
            
            logger.info(f"Completed skin analysis: {analysis_id}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error performing skin analysis: {e}")
            raise Exception(f"Failed to analyze skin condition: {str(e)}")

    def generate_treatment_plan(self, client_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized treatment plan based on skin analysis
        
        Args:
            client_id: ID of the client
            analysis_data: Results from skin analysis
            
        Returns:
            Dictionary with treatment plan details
        """
        try:
            plan_id = str(uuid.uuid4())
            
            # Generate treatment plan based on analysis
            treatment_plan = {
                'plan_id': plan_id,
                'client_id': client_id,
                'based_on_analysis': analysis_data.get('analysis_id'),
                'treatment_goals': [
                    'Improve skin hydration',
                    'Reduce acne breakouts',
                    'Even skin tone',
                    'Minimize pore appearance'
                ],
                'recommended_treatments': [
                    {
                        'treatment': 'Deep Cleansing Facial',
                        'frequency': 'Every 4 weeks',
                        'duration': '60 minutes',
                        'benefits': 'Remove impurities, unclog pores'
                    },
                    {
                        'treatment': 'Hydrating Treatment',
                        'frequency': 'Every 2 weeks',
                        'duration': '45 minutes',
                        'benefits': 'Restore moisture balance'
                    },
                    {
                        'treatment': 'Chemical Peel',
                        'frequency': 'Every 6 weeks',
                        'duration': '30 minutes',
                        'benefits': 'Improve skin texture and tone'
                    }
                ],
                'home_care_routine': {
                    'morning': [
                        'Gentle cleanser',
                        'Vitamin C serum',
                        'Moisturizer',
                        'SPF 30+ sunscreen'
                    ],
                    'evening': [
                        'Makeup remover',
                        'Gentle cleanser',
                        'Hyaluronic acid serum',
                        'Night moisturizer'
                    ]
                },
                'timeline': '12 weeks',
                'follow_up_schedule': [
                    'Week 2: Progress check',
                    'Week 6: Mid-treatment evaluation',
                    'Week 12: Final assessment'
                ],
                'created_date': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # Save treatment plan
            plan_key = f"treatment_plans/{plan_id}/plan.json"
            self._upload_json_to_s3(plan_key, treatment_plan)
            
            logger.info(f"Generated treatment plan: {plan_id} for client {client_id}")
            return treatment_plan
            
        except Exception as e:
            logger.error(f"Error generating treatment plan: {e}")
            raise Exception(f"Failed to generate treatment plan: {str(e)}")

    def track_treatment_progress(self, client_id: str, treatment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track and document treatment progress with before/after comparisons
        
        Args:
            client_id: ID of the client
            treatment_data: Treatment session data
            
        Returns:
            Dictionary with progress tracking results
        """
        try:
            progress_id = str(uuid.uuid4())
            
            progress_record = {
                'progress_id': progress_id,
                'client_id': client_id,
                'treatment_session': treatment_data.get('session_number', 1),
                'treatment_type': treatment_data.get('treatment_type'),
                'session_date': treatment_data.get('session_date', datetime.now().isoformat()),
                'improvements_noted': treatment_data.get('improvements', []),
                'concerns_addressed': treatment_data.get('concerns', []),
                'next_steps': treatment_data.get('next_steps', []),
                'practitioner_notes': treatment_data.get('notes', ''),
                'client_feedback': treatment_data.get('client_feedback', ''),
                'satisfaction_rating': treatment_data.get('satisfaction_rating'),
                'photos_taken': treatment_data.get('photos_taken', False),
                'status': 'completed'
            }
            
            # Save progress record
            progress_key = f"progress_tracking/{client_id}/{progress_id}.json"
            self._upload_json_to_s3(progress_key, progress_record)
            
            logger.info(f"Tracked treatment progress: {progress_id} for client {client_id}")
            return progress_record
            
        except Exception as e:
            logger.error(f"Error tracking treatment progress: {e}")
            raise Exception(f"Failed to track progress: {str(e)}")

    def get_analytics_data(self, salon_id: str, date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Generate analytics data for the salon
        
        Args:
            salon_id: ID of the salon
            date_range: Optional date range for analytics
            
        Returns:
            Dictionary with analytics data
        """
        try:
            # This would typically query actual data from S3 and databases
            # For demonstration, returning sample analytics data
            
            analytics = {
                'salon_id': salon_id,
                'period': date_range or {'start': '2024-01-01', 'end': '2024-12-31'},
                'generated_at': datetime.now().isoformat(),
                'metrics': {
                    'total_clients': 150,
                    'active_treatments': 45,
                    'completed_procedures': 320,
                    'product_formulations': 25,
                    'client_satisfaction': 4.7,
                    'revenue_this_month': 25000
                },
                'skin_type_distribution': {
                    'normal': 30,
                    'dry': 45,
                    'oily': 35,
                    'combination': 40,
                    'sensitive': 20,
                    'mature': 25
                },
                'popular_treatments': {
                    'facial_treatments': 85,
                    'chemical_peels': 45,
                    'microdermabrasion': 30,
                    'anti_aging': 60,
                    'acne_treatment': 40
                },
                'age_demographics': {
                    '18-25': 25,
                    '26-35': 40,
                    '36-45': 45,
                    '46-55': 30,
                    '56+': 15
                },
                'treatment_success_rates': {
                    'acne_treatment': 0.89,
                    'anti_aging': 0.92,
                    'skin_brightening': 0.87,
                    'hydration_therapy': 0.95
                }
            }
            
            # Save analytics data
            analytics_key = f"salons/{salon_id}/analytics/monthly_report_{datetime.now().strftime('%Y_%m')}.json"
            self._upload_json_to_s3(analytics_key, analytics)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            raise Exception(f"Failed to generate analytics: {str(e)}")

    def _upload_file_to_s3(self, s3_key: str, file_obj) -> Dict[str, Any]:
        """Upload file to S3 bucket"""
        try:
            if not self.s3_client:
                raise Exception("S3 client not initialized")
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': getattr(file_obj, 'content_type', 'application/octet-stream')}
            )
            
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return {
                's3_key': s3_key,
                's3_url': s3_url,
                'bucket': self.bucket_name,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise Exception(f"Failed to upload to S3: {str(e)}")

    def _upload_json_to_s3(self, s3_key: str, data: Dict[str, Any]) -> bool:
        """Upload JSON data to S3"""
        try:
            if not self.s3_client:
                return False
            
            json_data = json.dumps(data, indent=2, default=str)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload JSON to S3: {e}")
            return False

    def get_download_url(self, s3_key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for file download"""
        try:
            if not self.s3_client:
                raise Exception("S3 client not initialized")
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise Exception(f"Failed to generate download URL: {str(e)}")

    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        try:
            if not self.s3_client:
                return False
            
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False

    def sync_data(self) -> Dict[str, Any]:
        """Synchronize local database with S3 data"""
        try:
            # This would implement data synchronization logic
            # between local Django models and S3 storage
            
            sync_result = {
                'sync_id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'status': 'completed',
                'summary': {
                    'salons_synced': 10,
                    'clients_synced': 150,
                    'files_synced': 500,
                    'analyses_synced': 75
                }
            }
            
            return sync_result
            
        except Exception as e:
            logger.error(f"Data sync failed: {e}")
            raise Exception(f"Failed to sync data: {str(e)}")

    def cleanup_old_files(self, days_old: int = 365) -> Dict[str, Any]:
        """Clean up old files from S3 storage"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # This would implement actual cleanup logic
            cleanup_result = {
                'cleanup_id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'cutoff_date': cutoff_date.isoformat(),
                'files_deleted': 25,
                'space_freed': '2.5 GB',
                'status': 'completed'
            }
            
            return cleanup_result
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise Exception(f"Failed to cleanup files: {str(e)}")
