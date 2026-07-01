"""
URL patterns for Secure S3 Data Management API
"""
from django.urls import path
from .views import (
    CreateWorkspaceView,
    CreatePatientFolderView,
    UploadPatientFileView,
    DownloadPatientFileView,
    ListPatientFilesView,
    ListUserWorkspacesView,
    ListPatientFoldersView,
    GetAuditLogsView
)

app_name = 'secure_s3'

urlpatterns = [
    # Workspace management
    path('workspace/create/', CreateWorkspaceView.as_view(), name='create_workspace'),
    path('workspaces/', ListUserWorkspacesView.as_view(), name='list_workspaces'),
    
    # Patient folder management
    path('patient-folder/create/', CreatePatientFolderView.as_view(), name='create_patient_folder'),
    path('patient-folders/', ListPatientFoldersView.as_view(), name='list_patient_folders'),
    
    # File operations
    path('file/upload/', UploadPatientFileView.as_view(), name='upload_file'),
    path('file/download/<str:patient_id>/<str:file_id>/', DownloadPatientFileView.as_view(), name='download_file'),
    path('files/<str:patient_id>/', ListPatientFilesView.as_view(), name='list_patient_files'),
    
    # Audit and monitoring
    path('audit-logs/', GetAuditLogsView.as_view(), name='audit_logs'),
]
