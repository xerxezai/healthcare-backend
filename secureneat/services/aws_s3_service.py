import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging
import os
import uuid  # Import uuid

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        # Use a setting for prefix, default to 'secureneat-uploads'
        self.base_upload_key = getattr(
            settings, "AWS_S3_UPLOAD_KEY_PREFIX", "secureneat-uploads"
        )

    def _get_object_key(self, user_id, filename):
        """Generates a unique S3 object key."""
        # Sanitize filename to prevent path traversal issues
        safe_filename = os.path.basename(filename)
        # Use a UUID to ensure uniqueness and prevent overwrites
        unique_id = uuid.uuid4()
        # Structure: base_upload_key/user_id/uuid-filename.ext
        return f"{self.base_upload_key}/{user_id}/{unique_id}-{safe_filename}"

    def upload_file(
        self, file_obj, object_name, content_type="application/octet-stream"
    ):
        """
        Uploads a file-like object directly from the backend.
        (Kept for potential backend-initiated uploads, but frontend will use presigned URLs).
        """
        if not self.bucket_name:
            logger.error("S3_BUCKET_NAME is not configured.")
            return None, "S3 bucket not configured"
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_name,
                ExtraArgs={"ContentType": content_type},
            )
            # Construct URL (consider using get_presigned_url if files are private)
            # For public read files, this URL format is standard
            file_url = f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{object_name}"
            logger.info(
                f"File {object_name} uploaded to S3 bucket {self.bucket_name}. URL: {file_url}"
            )
            return file_url, None
        except ClientError as e:
            logger.error(f"S3 Upload Error: {e}")
            return None, str(e)
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            return None, "File upload failed due to an unexpected error."

    def generate_presigned_post(self, user_id, filename, content_type, expires_in=3600):
        """
        Generate a presigned URL and form fields for a direct S3 POST upload from a browser.
        Returns the presigned POST data, the generated object key, and an error message (if any).
        """
        if not self.bucket_name:
            logger.error("S3_BUCKET_NAME is not configured.")
            return None, None, "S3 bucket not configured"

        # Generate the unique object key for the file
        object_key = self._get_object_key(user_id, filename)

        try:
            # Generate the presigned POST data
            # Policy allows upload of this specific object_key with this content_type
            presigned_post_data = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=object_key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type}
                    # Add other conditions if needed, e.g., max file size
                    # ["content-length-range", 1, 10485760] # Max 10MB
                ],
                ExpiresIn=expires_in,  # URL expires in seconds
            )

            logger.info(
                f"Generated presigned POST for key {object_key} for user {user_id}"
            )
            # The response includes 'url' and 'fields'
            # The frontend will POST the file to 'url' with 'fields' as form data
            return presigned_post_data, object_key, None
        except ClientError as e:
            logger.error(
                f"S3 Presigned POST generation error for user {user_id}, file {filename}: {e}"
            )
            return None, None, str(e)
        except Exception as e:
            logger.error(f"Unexpected error generating S3 Presigned POST: {e}")
            return None, None, "Failed to generate S3 upload link."

    def get_file_content(self, object_key):
        """Retrieves file content from S3."""
        if not self.bucket_name:
            logger.error("S3_BUCKET_NAME is not configured.")
            return None
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=object_key
            )
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"S3 Get Object Error for key {object_key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting S3 object {object_key}: {e}")
            return None

    def list_files(self, prefix=""):
        """Lists files in the S3 bucket with an optional prefix."""
        if not self.bucket_name:
            logger.error("S3_BUCKET_NAME is not configured.")
            return []
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )
            return response.get("Contents", [])
        except ClientError as e:
            logger.error(f"S3 List Objects Error with prefix {prefix}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing S3 objects: {e}")
            return []


s3_service = S3Service()
