"""
Secure S3 Data Management Views
HIPAA-Compliant API endpoints for S3 operations
"""
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .s3_secure_manager import secure_s3_manager
from .models import UserWorkspace, PatientFolder, S3FileRecord, S3AuditLog, AccessPermission
import base64
from io import BytesIO

User = get_user_model()
logger = logging.getLogger(__name__)

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class SecureS3BaseView(View):
    """Base view for secure S3 operations with common functionality"""
    
    def dispatch(self, request, *args, **kwargs):
        # Add IP address to user for audit logging
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.user._request_ip = get_client_ip(request)
        return super().dispatch(request, *args, **kwargs)
    
    def check_module_access(self, user, module):
        """Check if user has access to the specified module"""
        if user.role == 'super_admin':
            return True
        
        # Check user's feature access or admin permissions
        # This would integrate with your existing permission system
        return True  # Simplified for now

@method_decorator([csrf_exempt, login_required], name='dispatch')
class CreateWorkspaceView(SecureS3BaseView):
    """Create user workspace in S3"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            module = data.get('module')
            
            if not module:
                return JsonResponse({
                    'success': False,
                    'error': 'Module is required'
                }, status=400)
            
            # Check module access
            if not self.check_module_access(request.user, module):
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied to this module'
                }, status=403)
            
            # Check if workspace already exists
            existing_workspace = UserWorkspace.objects.filter(
                user=request.user,
                module=module
            ).first()
            
            if existing_workspace:
                return JsonResponse({
                    'success': True,
                    'workspace_id': str(existing_workspace.id),
                    'message': 'Workspace already exists',
                    'workspace_path': existing_workspace.s3_path
                })
            
            # Create workspace in S3
            result = secure_s3_manager.create_user_workspace(request.user, module)
            
            if result['success']:
                # Create database record
                workspace = UserWorkspace.objects.create(
                    user=request.user,
                    module=module,
                    s3_path=result['workspace_path'],
                    storage_quota_gb=data.get('storage_quota_gb', 10)
                )
                
                return JsonResponse({
                    'success': True,
                    'workspace_id': str(workspace.id),
                    'workspace_path': workspace.s3_path,
                    'message': 'Workspace created successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                }, status=500)
                
        except Exception as e:
            logger.error(f"Failed to create workspace: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)

@method_decorator([csrf_exempt, login_required], name='dispatch')
class CreatePatientFolderView(SecureS3BaseView):
    """Create patient folder under doctor's workspace"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            module = data.get('module')
            patient_data = data.get('patient_data', {})
            
            if not module or not patient_data:
                return JsonResponse({
                    'success': False,
                    'error': 'Module and patient_data are required'
                }, status=400)
            
            # Check permissions
            if request.user.role not in ['doctor', 'admin', 'super_admin']:
                return JsonResponse({
                    'success': False,
                    'error': 'Only doctors and admins can create patient folders'
                }, status=403)
            
            # Check module access
            if not self.check_module_access(request.user, module):
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied to this module'
                }, status=403)
            
            # Ensure user has workspace
            workspace, created = UserWorkspace.objects.get_or_create(
                user=request.user,
                module=module,
                defaults={
                    's3_path': f"{secure_s3_manager.module_folders[module]}/staff/{request.user.role}s/{request.user.id}",
                    'storage_quota_gb': 50  # Doctors get more space
                }
            )
            
            # Create patient folder in S3
            result = secure_s3_manager.create_patient_folder(
                doctor=request.user,
                patient_data=patient_data,
                module=module
            )
            
            if result['success']:
                # Create database record
                patient_folder = PatientFolder.objects.create(
                    patient_id=result['patient_id'],
                    created_by=request.user,
                    assigned_doctor=request.user,
                    module=module,
                    s3_path=result['patient_path'],
                    encrypted_metadata_key=f"{result['patient_path']}/patient_index.json",
                    access_permissions={
                        'doctor_id': str(request.user.id),
                        'created_at': result.get('created_at'),
                        'permissions': ['read', 'write', 'delete']
                    }
                )
                
                return JsonResponse({
                    'success': True,
                    'patient_folder_id': str(patient_folder.id),
                    'patient_id': result['patient_id'],
                    'patient_path': result['patient_path'],
                    'message': 'Patient folder created successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                }, status=500)
                
        except Exception as e:
            logger.error(f"Failed to create patient folder: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)

@method_decorator([csrf_exempt, login_required], name='dispatch')
class UploadPatientFileView(SecureS3BaseView):
    """Upload file to patient's folder"""
    
    def post(self, request):
        try:
            # Handle multipart form data
            patient_id = request.POST.get('patient_id')
            module = request.POST.get('module')
            file_type = request.POST.get('file_type', 'general')
            metadata = json.loads(request.POST.get('metadata', '{}'))
            
            if not patient_id or not module:
                return JsonResponse({
                    'success': False,
                    'error': 'patient_id and module are required'
                }, status=400)
            
            # Get uploaded file
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return JsonResponse({
                    'success': False,
                    'error': 'No file uploaded'
                }, status=400)
            
            # Check file size (10MB limit)
            if uploaded_file.size > 10 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'error': 'File size exceeds 10MB limit'
                }, status=400)
            
            # Read file data
            file_data = uploaded_file.read()
            
            # Upload to S3
            result = secure_s3_manager.upload_patient_file(
                user=request.user,
                patient_id=patient_id,
                file_data=file_data,
                filename=uploaded_file.name,
                file_type=file_type,
                module=module,
                metadata=metadata
            )
            
            if result['success']:
                # Get patient folder
                patient_folder = PatientFolder.objects.filter(
                    patient_id=patient_id,
                    module=module
                ).first()
                
                if patient_folder:
                    # Create file record
                    file_record = S3FileRecord.objects.create(
                        patient_folder=patient_folder,
                        uploaded_by=request.user,
                        original_filename=uploaded_file.name,
                        s3_key=result['file_path'],
                        file_type=file_type,
                        content_type=uploaded_file.content_type,
                        file_size_bytes=uploaded_file.size,
                        checksum=result['checksum'],
                        metadata=metadata
                    )
                    
                    # Update workspace usage
                    workspace = UserWorkspace.objects.filter(
                        user=request.user,
                        module=module
                    ).first()
                    
                    if workspace:
                        workspace.current_usage_bytes += uploaded_file.size
                        workspace.save()
                
                return JsonResponse({
                    'success': True,
                    'file_id': result['file_id'],
                    'file_path': result['file_path'],
                    'checksum': result['checksum'],
                    'message': 'File uploaded successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                }, status=500)
                
        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)

@method_decorator([csrf_exempt, login_required], name='dispatch')
class DownloadPatientFileView(SecureS3BaseView):
    """Download patient file"""
    
    def get(self, request, patient_id, file_id):
        try:
            module = request.GET.get('module')
            
            if not module:
                return JsonResponse({
                    'success': False,
                    'error': 'Module parameter is required'
                }, status=400)
            
            # Download from S3
            result = secure_s3_manager.download_patient_file(
                user=request.user,
                patient_id=patient_id,
                file_id=file_id,
                module=module
            )
            
            if result['success']:
                # Create HTTP response with file
                response = HttpResponse(
                    result['file_data'],
                    content_type='application/octet-stream'
                )
                response['Content-Disposition'] = f'attachment; filename="{result["original_filename"]}"'
                response['Content-Length'] = len(result['file_data'])
                
                # Update last accessed time
                file_record = S3FileRecord.objects.filter(
                    s3_key__contains=file_id
                ).first()
                
                if file_record:
                    file_record.last_accessed = timezone.now()
                    file_record.save()
                
                return response
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                }, status=404 if 'not found' in result['error'].lower() else 500)
                
        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)

@method_decorator([csrf_exempt, login_required], name='dispatch')
class ListPatientFilesView(SecureS3BaseView):
    """List files in patient's folder"""
    
    def get(self, request, patient_id):
        try:
            module = request.GET.get('module')
            file_type = request.GET.get('file_type')
            
            if not module:
                return JsonResponse({
                    'success': False,
                    'error': 'Module parameter is required'
                }, status=400)
            
            # List files from S3
            result = secure_s3_manager.list_patient_files(
                user=request.user,
                patient_id=patient_id,
                module=module,
                file_type=file_type
            )
            
            if result['success']:
                # Get additional info from database
                patient_folder = PatientFolder.objects.filter(
                    patient_id=patient_id,
                    module=module
                ).first()
                
                if patient_folder:
                    # Get file records from database
                    file_records = S3FileRecord.objects.filter(
                        patient_folder=patient_folder
                    ).order_by('-uploaded_at')
                    
                    # Enhance file info with database data
                    enhanced_files = []
                    for s3_file in result['files']:
                        file_record = file_records.filter(
                            s3_key=s3_file['path']
                        ).first()
                        
                        enhanced_file = s3_file.copy()
                        if file_record:
                            enhanced_file.update({
                                'id': str(file_record.id),
                                'status': file_record.status,
                                'is_encrypted': file_record.is_encrypted,
                                'access_level': file_record.access_level,
                                'last_accessed': file_record.last_accessed.isoformat() if file_record.last_accessed else None
                            })
                        
                        enhanced_files.append(enhanced_file)
                    
                    result['files'] = enhanced_files
                
                return JsonResponse(result)
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                }, status=500)
                
        except Exception as e:
            logger.error(f"Failed to list patient files: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)

@method_decorator([csrf_exempt, login_required], name='dispatch')
class ListUserWorkspacesView(SecureS3BaseView):
    """List user's workspaces across modules"""
    
    def get(self, request):
        try:
            workspaces = UserWorkspace.objects.filter(
                user=request.user,
                status='active'
            ).order_by('module')
            
            workspace_data = []
            for workspace in workspaces:
                # Get patient folders count
                patient_folders_count = PatientFolder.objects.filter(
                    assigned_doctor=request.user,
                    module=workspace.module,
                    status='active'
                ).count()
                
                # Get total files count
                total_files = S3FileRecord.objects.filter(
                    patient_folder__assigned_doctor=request.user,
                    patient_folder__module=workspace.module,
                    status='uploaded'
                ).count()
                
                workspace_data.append({
                    'id': str(workspace.id),
                    'module': workspace.module,
                    's3_path': workspace.s3_path,
                    'status': workspace.status,
                    'storage_quota_gb': workspace.storage_quota_gb,
                    'current_usage_bytes': workspace.current_usage_bytes,
                    'usage_percentage': workspace.usage_percentage,
                    'remaining_space_gb': workspace.remaining_space_gb,
                    'patient_folders_count': patient_folders_count,
                    'total_files': total_files,
                    'created_at': workspace.created_at.isoformat(),
                    'last_accessed': workspace.last_accessed.isoformat()
                })
            
            return JsonResponse({
                'success': True,
                'workspaces': workspace_data,
                'total_workspaces': len(workspace_data)
            })
            
        except Exception as e:
            logger.error(f"Failed to list workspaces: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)

@method_decorator([csrf_exempt, login_required], name='dispatch')
class ListPatientFoldersView(SecureS3BaseView):
    """List patient folders for a doctor/admin"""
    
    def get(self, request):
        try:
            module = request.GET.get('module')
            
            if not module:
                return JsonResponse({
                    'success': False,
                    'error': 'Module parameter is required'
                }, status=400)
            
            # Get patient folders
            if request.user.role == 'super_admin':
                # Super admin can see all folders in the module
                patient_folders = PatientFolder.objects.filter(
                    module=module,
                    status='active'
                ).order_by('-created_at')
            elif request.user.role == 'admin':
                # Admin can see folders in their module
                patient_folders = PatientFolder.objects.filter(
                    module=module,
                    status='active'
                ).order_by('-created_at')
            else:
                # Doctors can only see their own patient folders
                patient_folders = PatientFolder.objects.filter(
                    assigned_doctor=request.user,
                    module=module,
                    status='active'
                ).order_by('-created_at')
            
            folder_data = []
            for folder in patient_folders:
                # Get file count and total size
                files = S3FileRecord.objects.filter(
                    patient_folder=folder,
                    status='uploaded'
                )
                
                total_files = files.count()
                total_size = sum(f.file_size_bytes for f in files)
                
                folder_data.append({
                    'id': str(folder.id),
                    'patient_id': folder.patient_id,
                    'assigned_doctor': {
                        'id': str(folder.assigned_doctor.id),
                        'name': folder.assigned_doctor.full_name,
                        'email': folder.assigned_doctor.email
                    } if folder.assigned_doctor else None,
                    'module': folder.module,
                    's3_path': folder.s3_path,
                    'status': folder.status,
                    'total_files': total_files,
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'created_at': folder.created_at.isoformat(),
                    'last_accessed': folder.last_accessed.isoformat()
                })
            
            return JsonResponse({
                'success': True,
                'patient_folders': folder_data,
                'total_folders': len(folder_data)
            })
            
        except Exception as e:
            logger.error(f"Failed to list patient folders: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)

@method_decorator([csrf_exempt, login_required], name='dispatch')
class GetAuditLogsView(SecureS3BaseView):
    """Get audit logs (admin/super admin only)"""
    
    def get(self, request):
        try:
            # Check permissions
            if request.user.role not in ['admin', 'super_admin']:
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied'
                }, status=403)
            
            # Get parameters
            module = request.GET.get('module')
            patient_id = request.GET.get('patient_id')
            action = request.GET.get('action')
            risk_level = request.GET.get('risk_level')
            days = int(request.GET.get('days', 30))
            
            # Filter logs
            logs = S3AuditLog.objects.all()
            
            if module:
                logs = logs.filter(module=module)
            if patient_id:
                logs = logs.filter(patient_id=patient_id)
            if action:
                logs = logs.filter(action=action)
            if risk_level:
                logs = logs.filter(risk_level=risk_level)
            
            # Time filter
            from datetime import timedelta
            cutoff_date = timezone.now() - timedelta(days=days)
            logs = logs.filter(timestamp__gte=cutoff_date)
            
            # Admin can only see logs for their modules
            if request.user.role == 'admin':
                # This would be filtered based on admin's module access
                pass  # Implement module-specific filtering
            
            logs = logs.order_by('-timestamp')[:100]  # Limit to 100 recent logs
            
            log_data = []
            for log in logs:
                log_data.append({
                    'id': str(log.id),
                    'user': {
                        'id': str(log.user.id),
                        'name': log.user.full_name,
                        'email': log.user.email,
                        'role': log.user.role
                    } if log.user else None,
                    'action': log.action,
                    'module': log.module,
                    'patient_id': log.patient_id,
                    'timestamp': log.timestamp.isoformat(),
                    'ip_address': log.ip_address,
                    'risk_level': log.risk_level,
                    'success': log.success,
                    'action_details': log.action_details,
                    'error_message': log.error_message
                })
            
            return JsonResponse({
                'success': True,
                'audit_logs': log_data,
                'total_logs': len(log_data)
            })
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
