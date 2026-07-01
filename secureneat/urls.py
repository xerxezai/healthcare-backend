from django.urls import path
from . import views_main as views

app_name = 'secureneat'

urlpatterns = [
    path('upload-s3/', views.DocumentUploadS3View.as_view(), name='document_upload_s3'),
    path('process-document/', views.DocumentProcessView.as_view(), name='document_process'),
    path('generate-mcq/', views.GenerateMCQView.as_view(), name='generate_mcq'),
    
    # S3 Library endpoints
    path('library/categories/', views.S3LibraryCategoriesView.as_view(), name='s3_library_categories'),
    path('library/books/', views.S3LibraryBooksView.as_view(), name='s3_library_books'),
    path('library/generate-mcq/', views.S3LibraryMCQGenerateView.as_view(), name='s3_library_generate_mcq'),
    path('library/upload/', views.S3LibraryUploadView.as_view(), name='s3_library_upload'),
]