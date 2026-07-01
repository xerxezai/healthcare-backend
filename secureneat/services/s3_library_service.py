import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging
import os
from typing import List, Dict, Optional, Tuple
import mimetypes

logger = logging.getLogger(__name__)


class S3LibraryService:
    """
    Service for managing book collections and notes in AWS S3.
    Organizes content in structured folders for easy access.
    """
    
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        
        # Organized folder structure for your library
        self.library_prefixes = {
            'medical_books': 'library/medical-books/',
            'nursing_books': 'library/nursing-books/',
            'research_papers': 'library/research-papers/',
            'study_notes': 'library/study-notes/',
            'reference_materials': 'library/reference-materials/',
            'exam_prep': 'library/exam-prep/',
            'clinical_guidelines': 'library/clinical-guidelines/',
            'medical_journals': 'library/medical-journals/'
        }

    def list_book_categories(self) -> List[Dict]:
        """
        Lists all available book categories with file counts.
        """
        categories = []
        
        for category_name, prefix in self.library_prefixes.items():
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    Delimiter='/'
                )
                
                # Count files in this category
                file_count = len(response.get('Contents', []))
                
                # Get subcategories (folders)
                subcategories = []
                for common_prefix in response.get('CommonPrefixes', []):
                    folder_name = common_prefix['Prefix'].replace(prefix, '').rstrip('/')
                    subcategories.append(folder_name)
                
                categories.append({
                    'name': category_name.replace('_', ' ').title(),
                    'key': category_name,
                    'prefix': prefix,
                    'file_count': file_count,
                    'subcategories': subcategories
                })
                
            except ClientError as e:
                logger.error(f"Error listing category {category_name}: {e}")
                
        return categories

    def list_books_in_category(self, category: str, subcategory: Optional[str] = None) -> List[Dict]:
        """
        Lists all books in a specific category.
        
        Args:
            category: Category key (e.g., 'medical_books')
            subcategory: Optional subcategory folder
        """
        if category not in self.library_prefixes:
            return []
            
        prefix = self.library_prefixes[category]
        if subcategory:
            prefix += f"{subcategory}/"
            
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            books = []
            for obj in response.get('Contents', []):
                # Skip folder markers
                if obj['Key'].endswith('/'):
                    continue
                    
                filename = os.path.basename(obj['Key'])
                file_size = obj['Size']
                last_modified = obj['LastModified']
                
                # Determine file type
                mime_type, _ = mimetypes.guess_type(filename)
                file_extension = os.path.splitext(filename)[1].lower()
                
                books.append({
                    'filename': filename,
                    'key': obj['Key'],
                    'size': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'last_modified': last_modified.isoformat(),
                    'mime_type': mime_type,
                    'extension': file_extension,
                    'category': category,
                    'subcategory': subcategory,
                    'download_url': self.generate_download_url(obj['Key'])
                })
                
            return sorted(books, key=lambda x: x['last_modified'], reverse=True)
            
        except ClientError as e:
            logger.error(f"Error listing books in category {category}: {e}")
            return []

    def search_books(self, search_term: str, categories: Optional[List[str]] = None) -> List[Dict]:
        """
        Searches for books across categories by filename.
        
        Args:
            search_term: Term to search for in filenames
            categories: Optional list of categories to search in
        """
        search_term = search_term.lower()
        results = []
        
        search_categories = categories if categories else list(self.library_prefixes.keys())
        
        for category in search_categories:
            books = self.list_books_in_category(category)
            matching_books = [
                book for book in books 
                if search_term in book['filename'].lower()
            ]
            results.extend(matching_books)
            
        return sorted(results, key=lambda x: x['last_modified'], reverse=True)

    def get_book_content(self, s3_key: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Downloads book content from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Tuple of (content_bytes, error_message)
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            content = response['Body'].read()
            logger.info(f"Successfully downloaded {s3_key} from S3")
            return content, None
            
        except ClientError as e:
            error_msg = f"Failed to download {s3_key}: {e}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error downloading {s3_key}: {e}"
            logger.error(error_msg)
            return None, error_msg

    def generate_download_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Generates a presigned URL for downloading a book.
        
        Args:
            s3_key: S3 object key
            expires_in: URL expiration time in seconds
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating download URL for {s3_key}: {e}")
            return ""

    def upload_book_to_library(self, file_obj, filename: str, category: str, 
                             subcategory: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Uploads a new book to the S3 library.
        
        Args:
            file_obj: File object to upload
            filename: Original filename
            category: Category to upload to
            subcategory: Optional subcategory
            
        Returns:
            Tuple of (s3_key, error_message)
        """
        if category not in self.library_prefixes:
            return None, f"Invalid category: {category}"
            
        # Construct S3 key
        prefix = self.library_prefixes[category]
        if subcategory:
            prefix += f"{subcategory}/"
            
        s3_key = f"{prefix}{filename}"
        
        try:
            # Determine content type
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'
                
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': content_type}
            )
            
            logger.info(f"Successfully uploaded {filename} to {s3_key}")
            return s3_key, None
            
        except ClientError as e:
            error_msg = f"Failed to upload {filename}: {e}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error uploading {filename}: {e}"
            logger.error(error_msg)
            return None, error_msg

    def get_book_metadata(self, s3_key: str) -> Optional[Dict]:
        """
        Gets metadata for a specific book.
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat(),
                'content_type': response.get('ContentType', 'unknown'),
                'etag': response['ETag'].strip('"'),
            }
            
        except ClientError as e:
            logger.error(f"Error getting metadata for {s3_key}: {e}")
            return None


# Singleton instance
s3_library_service = S3LibraryService()
