"""
Registration Document Upload Views with Soft Coding
Handles file uploads during registration process with AWS S3 integration
"""

import os
import uuid
import mimetypes
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
import boto3
import logging

from .registration_document_models import (
    RegistrationDocumentType, 
    RegistrationDocument, 
    RegistrationDocumentTemplate
)

logger = logging.getLogger(__name__)

class RegistrationDocumentUploadView(APIView):
    """
    Handle document uploads during registration with comprehensive soft coding
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    # Soft-coded configuration for easy customization
    UPLOAD_CONFIG = {
        'file_validation': {
            'max_file_size_mb': 10,
            'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.tiff'],
            'allowed_mime_types': [
                'application/pdf',
                'image/jpeg', 'image/jpg', 'image/png', 'image/tiff',
                'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ],
            'require_virus_scan': True,
            'min_file_size_bytes': 1024  # 1KB minimum
        },
        'security_settings': {
            'encrypt_files': True,
            'generate_unique_names': True,
            'track_upload_ip': True,
            'rate_limit_per_hour': 20
        },
        's3_settings': {
            'bucket_name': getattr(settings, 'S3_BUCKET_NAME', 'healthcare-documents'),
            'storage_class': 'STANDARD_IA',  # Infrequent Access for cost optimization
            'server_side_encryption': 'AES256',
            'public_read': False
        },
        'response_messages': {
            'success': '✅ Document uploaded successfully',
            'file_too_large': '❌ File size exceeds limit',
            'invalid_type': '❌ File type not allowed',
            'upload_failed': '❌ Upload failed, please try again',
            'rate_limited': '❌ Too many uploads, please wait'
        }
    }
    
    def __init__(self):
        super().__init__()
        self.s3_client = self._initialize_s3_client()
    
    def _initialize_s3_client(self):
        """Initialize AWS S3 client with soft-coded configuration"""
        try:
            return boto3.client(
                's3',
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                region_name=getattr(settings, 'AWS_SES_REGION', 'ap-south-1')
            )
        except Exception as e:
            logger.warning(f"S3 client initialization failed: {e}")
            return None
    
    def _validate_file(self, file):
        """
        Comprehensive file validation with soft-coded rules
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        config = self.UPLOAD_CONFIG['file_validation']
        
        # File size validation
        if file.size > config['max_file_size_mb'] * 1024 * 1024:
            validation_results['is_valid'] = False
            validation_results['errors'].append(
                f"File size ({file.size / (1024*1024):.1f}MB) exceeds limit ({config['max_file_size_mb']}MB)"
            )
        
        if file.size < config['min_file_size_bytes']:
            validation_results['is_valid'] = False
            validation_results['errors'].append("File appears to be empty or corrupted")
        
        # File extension validation
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in config['allowed_extensions']:
            validation_results['is_valid'] = False
            validation_results['errors'].append(
                f"File type '{file_extension}' not allowed. Allowed types: {', '.join(config['allowed_extensions'])}"
            )
        
        # MIME type validation
        mime_type, _ = mimetypes.guess_type(file.name)
        if mime_type and mime_type not in config['allowed_mime_types']:
            validation_results['warnings'].append(f"Unusual MIME type detected: {mime_type}")
        
        # Store file information
        validation_results['file_info'] = {
            'original_name': file.name,
            'size_bytes': file.size,
            'size_mb': round(file.size / (1024*1024), 2),
            'extension': file_extension,
            'mime_type': mime_type or 'unknown'
        }
        
        return validation_results
    
    def _generate_s3_key(self, user_email, document_type, file_extension):
        """
        Generate S3 key with soft-coded structure for organization
        """
        timestamp = datetime.now().strftime('%Y/%m/%d')
        unique_id = uuid.uuid4().hex[:12]
        
        # Soft-coded path structure
        key_template = "{base_path}/{user_hash}/{document_type}/{timestamp}/{unique_id}{extension}"
        
        # Hash user email for privacy (first 8 characters of hash)
        import hashlib
        user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:8]
        
        return key_template.format(
            base_path="registration-documents",
            user_hash=user_hash,
            document_type=document_type.lower().replace(' ', '-'),
            timestamp=timestamp,
            unique_id=unique_id,
            extension=file_extension
        )
    
    def _upload_to_s3(self, file, s3_key):
        """
        Upload file to S3 with soft-coded security settings
        """
        if not self.s3_client:
            raise Exception("S3 client not available")
        
        try:
            s3_config = self.UPLOAD_CONFIG['s3_settings']
            
            # Upload with server-side encryption
            self.s3_client.upload_fileobj(
                file,
                s3_config['bucket_name'],
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': s3_config['server_side_encryption'],
                    'StorageClass': s3_config['storage_class'],
                    'ContentType': file.content_type or 'application/octet-stream'
                }
            )
            
            # Generate pre-signed URL for secure access
            file_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': s3_config['bucket_name'], 'Key': s3_key},
                ExpiresIn=3600  # 1 hour expiry
            )
            
            return {
                'success': True,
                's3_key': s3_key,
                'file_url': file_url,
                'bucket': s3_config['bucket_name']
            }
            
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def post(self, request):
        """Handle document upload with comprehensive validation and soft coding"""
        try:
            # Extract data with soft-coded validation
            file = request.FILES.get('file')
            document_type_id = request.data.get('document_type_id')
            user_email = request.data.get('user_email')  # For registration uploads
            
            if not file:
                return Response({
                    'success': False,
                    'error': 'No file provided',
                    'code': 'NO_FILE'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not document_type_id:
                return Response({
                    'success': False,
                    'error': 'Document type is required',
                    'code': 'NO_DOCUMENT_TYPE'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get document type
            try:
                document_type = RegistrationDocumentType.objects.get(id=document_type_id, is_active=True)
            except RegistrationDocumentType.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Invalid document type',
                    'code': 'INVALID_DOCUMENT_TYPE'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate file
            validation = self._validate_file(file)
            if not validation['is_valid']:
                return Response({
                    'success': False,
                    'error': 'File validation failed',
                    'validation_errors': validation['errors'],
                    'code': 'VALIDATION_FAILED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate S3 key
            file_extension = os.path.splitext(file.name)[1].lower()
            s3_key = self._generate_s3_key(user_email or 'anonymous', document_type.name, file_extension)
            
            # Upload to S3
            upload_result = self._upload_to_s3(file, s3_key)
            if not upload_result['success']:
                return Response({
                    'success': False,
                    'error': self.UPLOAD_CONFIG['response_messages']['upload_failed'],
                    'details': upload_result.get('error'),
                    'code': 'UPLOAD_FAILED'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Create database record (for registered users)
            document_record = None
            if user_email and hasattr(request, 'user') and request.user.is_authenticated:
                document_record = RegistrationDocument.objects.create(
                    user=request.user,
                    document_type=document_type,
                    file=s3_key,  # Store S3 key as file path
                    original_filename=file.name,
                    file_size=file.size,
                    mime_type=file.content_type or 'unknown',
                    upload_ip=request.META.get('REMOTE_ADDR'),
                    validation_status=validation,
                    metadata={
                        'upload_timestamp': datetime.now().isoformat(),
                        's3_bucket': upload_result['bucket'],
                        's3_key': upload_result['s3_key'],
                        'upload_config_version': '1.0'
                    }
                )
            
            # Success response with soft-coded message
            response_data = {
                'success': True,
                'message': self.UPLOAD_CONFIG['response_messages']['success'],
                'file_info': validation['file_info'],
                'document_id': document_record.id if document_record else None,
                'upload_details': {
                    's3_key': upload_result['s3_key'],
                    'file_url': upload_result['file_url'],
                    'document_type': document_type.name,
                    'validation_summary': validation.get('warnings', [])
                }
            }
            
            logger.info(f"Document uploaded successfully: {s3_key} for {user_email}")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Document upload error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error during upload',
                'code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RegistrationDocumentTypesView(APIView):
    """
    Get available document types for registration with soft-coded configuration
    """
    permission_classes = [AllowAny]
    
    # Soft-coded configuration for document requirements
    DOCUMENT_REQUIREMENTS_CONFIG = {
        'default_role': 'general_doctor',
        'required_document_minimum': 3,
        'categories': {
            'identity': {
                'display_name': 'Identity Verification',
                'description': 'Documents to verify your identity',
                'icon': '🆔',
                'priority': 1
            },
            'license': {
                'display_name': 'Medical License',
                'description': 'Professional medical licenses and registrations',
                'icon': '📋',
                'priority': 2
            },
            'education': {
                'display_name': 'Educational Credentials', 
                'description': 'Degrees, diplomas, and certifications',
                'icon': '🎓',
                'priority': 3
            },
            'experience': {
                'display_name': 'Work Experience',
                'description': 'Employment history and references',
                'icon': '💼',
                'priority': 4
            }
        },
        'help_messages': {
            'file_requirements': 'Files must be clear, readable, and in PDF, JPG, or PNG format',
            'size_limit': 'Maximum file size: 10MB per document',
            'quality_tips': 'Ensure all text is clearly visible and documents are complete'
        }
    }
    
    def get(self, request):
        """Get available document types with soft-coded organization"""
        try:
            role = request.GET.get('role', self.DOCUMENT_REQUIREMENTS_CONFIG['default_role'])
            
            # Get document types
            document_types = RegistrationDocumentType.objects.filter(is_active=True)
            
            # Organize by category with soft-coded configuration
            categories = {}
            config = self.DOCUMENT_REQUIREMENTS_CONFIG
            
            for doc_type in document_types:
                category = doc_type.category
                if category not in categories:
                    category_config = config['categories'].get(category, {})
                    categories[category] = {
                        'name': category,
                        'display_name': category_config.get('display_name', category.title()),
                        'description': category_config.get('description', ''),
                        'icon': category_config.get('icon', '📄'),
                        'priority': category_config.get('priority', 999),
                        'documents': []
                    }
                
                categories[category]['documents'].append({
                    'id': doc_type.id,
                    'name': doc_type.name,
                    'description': doc_type.description,
                    'is_required': doc_type.is_required,
                    'priority_level': doc_type.priority_level,
                    'file_size_limit_mb': doc_type.file_size_limit_mb,
                    'allowed_extensions': doc_type.allowed_extensions,
                    'help_text': doc_type.help_text,
                    'validation_rules': doc_type.validation_rules
                })
            
            # Sort categories by priority
            sorted_categories = sorted(
                categories.values(),
                key=lambda x: x['priority']
            )
            
            return Response({
                'success': True,
                'categories': sorted_categories,
                'requirements': {
                    'minimum_required': config['required_document_minimum'],
                    'help_messages': config['help_messages']
                },
                'upload_config': {
                    'max_file_size_mb': 10,
                    'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'],
                    'multiple_files_per_type': True
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching document types: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch document types'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RegistrationDocumentValidationView(APIView):
    """
    Validate uploaded documents with soft-coded validation rules
    """
    permission_classes = [AllowAny]
    
    # Soft-coded validation configuration
    VALIDATION_CONFIG = {
        'quality_checks': {
            'min_resolution_dpi': 300,
            'check_text_readability': True,
            'detect_blurriness': True,
            'check_completeness': True
        },
        'security_checks': {
            'virus_scan': True,
            'malware_detection': True,
            'file_integrity': True
        },
        'content_validation': {
            'check_document_type_match': True,
            'verify_required_fields': True,
            'validate_expiry_dates': True
        },
        'scoring_weights': {
            'quality': 0.4,
            'security': 0.3,
            'content': 0.3
        }
    }
    
    def post(self, request):
        """Validate document with comprehensive soft-coded checks"""
        try:
            document_id = request.data.get('document_id')
            
            if not document_id:
                return Response({
                    'success': False,
                    'error': 'Document ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                document = RegistrationDocument.objects.get(id=document_id)
            except RegistrationDocument.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Document not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Perform validation with soft-coded rules
            validation_results = self._validate_document(document)
            
            # Update document with validation results
            document.validation_status = validation_results
            document.save()
            
            return Response({
                'success': True,
                'validation_results': validation_results,
                'overall_score': validation_results.get('overall_score', 0),
                'recommendations': validation_results.get('recommendations', [])
            })
            
        except Exception as e:
            logger.error(f"Document validation error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Validation failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_document(self, document):
        """
        Comprehensive document validation with soft-coded rules
        """
        config = self.VALIDATION_CONFIG
        results = {
            'quality_score': 0,
            'security_score': 0,
            'content_score': 0,
            'overall_score': 0,
            'issues': [],
            'recommendations': [],
            'validation_timestamp': datetime.now().isoformat()
        }
        
        # Quality checks
        quality_checks = self._perform_quality_checks(document, config['quality_checks'])
        results['quality_score'] = quality_checks['score']
        results['issues'].extend(quality_checks['issues'])
        
        # Security checks
        security_checks = self._perform_security_checks(document, config['security_checks'])
        results['security_score'] = security_checks['score']
        results['issues'].extend(security_checks['issues'])
        
        # Content validation
        content_checks = self._perform_content_validation(document, config['content_validation'])
        results['content_score'] = content_checks['score']
        results['issues'].extend(content_checks['issues'])
        
        # Calculate overall score with soft-coded weights
        weights = config['scoring_weights']
        results['overall_score'] = (
            results['quality_score'] * weights['quality'] +
            results['security_score'] * weights['security'] +
            results['content_score'] * weights['content']
        )
        
        # Generate recommendations
        if results['overall_score'] < 70:
            results['recommendations'].append("Document quality could be improved")
        if results['quality_score'] < 60:
            results['recommendations'].append("Consider uploading a higher quality scan")
        if len(results['issues']) > 0:
            results['recommendations'].append("Please review and address the identified issues")
        
        return results
    
    def _perform_quality_checks(self, document, config):
        """Perform quality checks on document"""
        # Placeholder for quality checks
        # In production, this would include image analysis, OCR, etc.
        return {
            'score': 85,  # Mock score
            'issues': []
        }
    
    def _perform_security_checks(self, document, config):
        """Perform security checks on document"""
        # Placeholder for security checks
        # In production, this would include virus scanning, malware detection
        return {
            'score': 100,  # Mock score
            'issues': []
        }
    
    def _perform_content_validation(self, document, config):
        """Perform content validation on document"""
        # Placeholder for content validation
        # In production, this would include OCR text extraction and validation
        return {
            'score': 90,  # Mock score
            'issues': []
        }
