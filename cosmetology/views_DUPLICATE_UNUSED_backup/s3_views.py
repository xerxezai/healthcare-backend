"""
Cosmetology S3 Data Management Views
API endpoints for beauty and aesthetic practice management with cloud storage
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
import logging
import json

from ..models import (
    CosmetologySalon, CosmetologyClientS3, 
    CosmetologyFile, CosmetologyAnalysis
)
from ..services.s3_service import CosmetologyS3Service
from ..serializers import (
    CosmetologySalonSerializer, CosmetologyClientS3Serializer,
    CosmetologyFileSerializer, CosmetologyAnalysisSerializer
)

logger = logging.getLogger(__name__)

class CosmetologySalonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cosmetology salons/institutions with S3 integration
    """
    queryset = CosmetologySalon.objects.all()
    serializer_class = CosmetologySalonSerializer
    lookup_field = 'salon_id'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s3_service = CosmetologyS3Service()
    
    def create(self, request, *args, **kwargs):
        """Create new salon with S3 folder structure"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Create salon with S3 integration
            salon_data = serializer.validated_data
            s3_result = self.s3_service.create_cosmetology_salon(salon_data)
            
            # Update salon data with S3 information
            salon_data.update({
                'salon_id': s3_result['salon_id'],
                's3_folders': s3_result['s3_folders'],
                'created_by': request.user
            })
            
            salon = CosmetologySalon.objects.create(**salon_data)
            response_serializer = self.get_serializer(salon)
            
            return Response({
                'salon': response_serializer.data,
                's3_integration': s3_result,
                'message': 'Salon created successfully with S3 integration'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating salon: {e}")
            return Response({
                'error': 'Failed to create salon',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, salon_id=None):
        """Get analytics data for specific salon"""
        try:
            salon = get_object_or_404(CosmetologySalon, salon_id=salon_id)
            
            # Generate analytics data
            analytics_data = self.s3_service.get_analytics_data(str(salon.salon_id))
            
            return Response({
                'salon': salon.name,
                'analytics': analytics_data,
                'generated_at': timezone.now()
            })
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            return Response({
                'error': 'Failed to generate analytics',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CosmetologyClientS3ViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cosmetology clients with S3 integration
    """
    queryset = CosmetologyClientS3.objects.all()
    serializer_class = CosmetologyClientS3Serializer
    lookup_field = 'client_id'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s3_service = CosmetologyS3Service()
    
    def create(self, request, *args, **kwargs):
        """Register new client with S3 folder structure"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Get salon information
            salon_id = serializer.validated_data.get('salon_id')
            if isinstance(salon_id, CosmetologySalon):
                salon = salon_id
            else:
                salon = get_object_or_404(CosmetologySalon, salon_id=salon_id)
            
            # Register client with S3 integration
            client_data = serializer.validated_data
            s3_result = self.s3_service.register_client(str(salon.salon_id), client_data)
            
            # Create client record
            client_data.update({
                'client_id': s3_result['client_id'],
                'salon': salon,
                's3_folders': s3_result['s3_folders']
            })
            
            client = CosmetologyClientS3.objects.create(**client_data)
            response_serializer = self.get_serializer(client)
            
            return Response({
                'client': response_serializer.data,
                's3_integration': s3_result,
                'message': 'Client registered successfully with S3 integration'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error registering client: {e}")
            return Response({
                'error': 'Failed to register client',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def files(self, request, client_id=None):
        """Get all files for specific client"""
        try:
            client = get_object_or_404(CosmetologyClientS3, client_id=client_id)
            files = CosmetologyFile.objects.filter(client=client)
            
            files_data = []
            for file_obj in files:
                file_data = CosmetologyFileSerializer(file_obj).data
                file_data['download_url'] = self.s3_service.get_download_url(file_obj.s3_key)
                files_data.append(file_data)
            
            return Response({
                'client': f"{client.first_name} {client.last_name}",
                'files': files_data,
                'total_files': len(files_data)
            })
            
        except Exception as e:
            logger.error(f"Error fetching client files: {e}")
            return Response({
                'error': 'Failed to fetch client files',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CosmetologyFileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cosmetology files with S3 storage
    """
    queryset = CosmetologyFile.objects.all()
    serializer_class = CosmetologyFileSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'file_id'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s3_service = CosmetologyS3Service()
    
    def create(self, request, *args, **kwargs):
        """Upload file to S3 and create database record"""
        try:
            # Extract form data
            salon_id = request.data.get('salon_id')
            client_id = request.data.get('client_id')
            category = request.data.get('category')
            file_obj = request.FILES.get('file')
            description = request.data.get('description', '')
            
            if not file_obj:
                return Response({
                    'error': 'No file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not salon_id:
                return Response({
                    'error': 'Salon ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get salon and client objects
            salon = get_object_or_404(CosmetologySalon, salon_id=salon_id)
            client = None
            if client_id:
                client = get_object_or_404(CosmetologyClientS3, client_id=client_id)
            
            # Upload file using S3 service
            file_data = {
                'file': file_obj,
                'category': category
            }
            
            s3_result = self.s3_service.upload_treatment_file(
                str(salon.salon_id),
                str(client.client_id) if client else None,
                file_data
            )
            
            # Create database record
            file_record = CosmetologyFile.objects.create(
                file_id=s3_result['file_id'],
                salon=salon,
                client=client,
                original_name=s3_result['original_name'],
                filename=s3_result['filename'],
                file_size=s3_result['file_size'],
                content_type=s3_result['content_type'],
                category=s3_result['category'],
                s3_key=s3_result['s3_key'],
                s3_bucket=salon.s3_bucket or 'cosmetology-default',
                s3_url=s3_result['s3_url'],
                description=description,
                uploaded_by=request.user,
                status='uploaded'
            )
            
            serializer = self.get_serializer(file_record)
            
            return Response({
                'file': serializer.data,
                's3_result': s3_result,
                'message': 'File uploaded successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return Response({
                'error': 'Failed to upload file',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download_url(self, request, file_id=None):
        """Generate download URL for file"""
        try:
            file_obj = get_object_or_404(CosmetologyFile, file_id=file_id)
            
            # Generate presigned URL
            download_url = self.s3_service.get_download_url(file_obj.s3_key)
            
            # Update last accessed time
            file_obj.last_accessed = timezone.now()
            file_obj.save(update_fields=['last_accessed'])
            
            return Response({
                'file_name': file_obj.original_name,
                'download_url': download_url,
                'expires_in': '1 hour',
                'file_size': file_obj.file_size_formatted
            })
            
        except Exception as e:
            logger.error(f"Error generating download URL: {e}")
            return Response({
                'error': 'Failed to generate download URL',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, file_id=None):
        """Perform AI analysis on uploaded file"""
        try:
            file_obj = get_object_or_404(CosmetologyFile, file_id=file_id)
            analysis_type = request.data.get('analysis_type', 'skin_condition_analysis')
            
            # Perform analysis using S3 service
            analysis_result = self.s3_service.analyze_skin_condition(
                str(file_obj.file_id),
                analysis_type
            )
            
            # Create analysis record
            analysis_record = CosmetologyAnalysis.objects.create(
                analysis_id=analysis_result['analysis_id'],
                salon=file_obj.salon,
                client=file_obj.client,
                file=file_obj,
                analysis_type=analysis_result['analysis_type'],
                confidence_score=analysis_result['confidence_score'],
                analysis_results=analysis_result['results'],
                status='completed'
            )
            
            # Update file status
            file_obj.status = 'analyzed'
            file_obj.save(update_fields=['status'])
            
            return Response({
                'analysis': CosmetologyAnalysisSerializer(analysis_record).data,
                'message': 'Analysis completed successfully'
            })
            
        except Exception as e:
            logger.error(f"Error performing analysis: {e}")
            return Response({
                'error': 'Failed to perform analysis',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, *args, **kwargs):
        """Delete file from both S3 and database"""
        try:
            file_obj = self.get_object()
            
            # Delete from S3
            self.s3_service.delete_file(file_obj.s3_key)
            
            # Delete from database
            file_obj.delete()
            
            return Response({
                'message': 'File deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return Response({
                'error': 'Failed to delete file',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CosmetologyAnalysisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing AI analysis results
    """
    queryset = CosmetologyAnalysis.objects.all()
    serializer_class = CosmetologyAnalysisSerializer
    lookup_field = 'analysis_id'
    
    @action(detail=True, methods=['post'])
    def validate(self, request, analysis_id=None):
        """Validate analysis results by human expert"""
        try:
            analysis = get_object_or_404(CosmetologyAnalysis, analysis_id=analysis_id)
            
            validation_notes = request.data.get('validation_notes', '')
            is_valid = request.data.get('is_valid', True)
            
            # Update analysis validation
            analysis.validated_by = request.user
            analysis.validation_date = timezone.now()
            analysis.validation_notes = validation_notes
            analysis.status = 'validated' if is_valid else 'failed'
            analysis.save()
            
            return Response({
                'analysis_id': str(analysis.analysis_id),
                'validation_status': analysis.status,
                'validated_by': request.user.username,
                'message': 'Analysis validation completed'
            })
            
        except Exception as e:
            logger.error(f"Error validating analysis: {e}")
            return Response({
                'error': 'Failed to validate analysis',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Utility Views
def cosmetology_analytics_view(request):
    """Generate comprehensive analytics for cosmetology module"""
    try:
        # Get summary statistics
        total_salons = CosmetologySalon.objects.filter(status='active').count()
        total_clients = CosmetologyClientS3.objects.filter(status='active').count()
        total_files = CosmetologyFile.objects.filter(status='uploaded').count()
        total_analyses = CosmetologyAnalysis.objects.filter(status='completed').count()
        
        # Get recent activity
        recent_salons = CosmetologySalon.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        recent_clients = CosmetologyClientS3.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Skin type distribution
        skin_types = CosmetologyClientS3.objects.values('skin_type').annotate(
            count=Count('skin_type')
        ).order_by('-count')
        
        # Analysis statistics
        analysis_stats = CosmetologyAnalysis.objects.values('analysis_type').annotate(
            count=Count('analysis_type')
        ).order_by('-count')[:10]
        
        analytics_data = {
            'overview': {
                'total_salons': total_salons,
                'total_clients': total_clients,
                'total_files': total_files,
                'total_analyses': total_analyses,
                'recent_salons': recent_salons,
                'recent_clients': recent_clients
            },
            'skin_type_distribution': list(skin_types),
            'popular_analyses': list(analysis_stats),
            'generated_at': timezone.now().isoformat()
        }
        
        return JsonResponse(analytics_data)
        
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        return JsonResponse({
            'error': 'Failed to generate analytics',
            'details': str(e)
        }, status=500)

def cosmetology_sync_view(request):
    """Synchronize S3 data with local database"""
    try:
        s3_service = CosmetologyS3Service()
        sync_result = s3_service.sync_data()
        
        return JsonResponse({
            'sync_result': sync_result,
            'message': 'Data synchronization completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error during sync: {e}")
        return JsonResponse({
            'error': 'Failed to synchronize data',
            'details': str(e)
        }, status=500)

def cosmetology_cleanup_view(request):
    """Clean up old files from S3 storage"""
    try:
        days_old = int(request.GET.get('days_old', 365))
        s3_service = CosmetologyS3Service()
        cleanup_result = s3_service.cleanup_old_files(days_old)
        
        return JsonResponse({
            'cleanup_result': cleanup_result,
            'message': 'File cleanup completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return JsonResponse({
            'error': 'Failed to cleanup files',
            'details': str(e)
        }, status=500)
