from rest_framework import serializers
from .models import S3UploadedFile, S3LibraryBook, MCQGenerationHistory

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

class S3UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = S3UploadedFile
        fields = ['id', 'file_key', 'original_filename', 'content_type', 'upload_time', 'file_url']

class DocumentProcessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    summary = serializers.CharField()
    # analysis = serializers.CharField() # The Node.js version didn't return full analysis
    extractedText = serializers.CharField(source='extracted_text_snippet')


class S3LibraryBookSerializer(serializers.ModelSerializer):
    size_mb = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()
    
    class Meta:
        model = S3LibraryBook
        fields = [
            'id', 'title', 's3_key', 'category', 'subcategory', 'filename',
            'file_size', 'size_mb', 'content_type', 'author', 'publisher',
            'publication_year', 'isbn', 'description', 'tags', 'tag_list',
            'date_added', 'last_accessed', 'access_count', 'mcq_generation_count',
            'last_mcq_generated'
        ]
        read_only_fields = [
            'id', 's3_key', 'file_size', 'date_added', 'last_accessed',
            'access_count', 'mcq_generation_count', 'last_mcq_generated'
        ]


class MCQGenerationHistorySerializer(serializers.ModelSerializer):
    library_book_title = serializers.CharField(source='library_book.title', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = MCQGenerationHistory
        fields = [
            'id', 'user', 'user_username', 'library_book', 'library_book_title',
            's3_key', 'filename', 'num_questions', 'generation_type',
            'questions_generated', 'generation_successful', 'error_message',
            'created_at', 'generation_time_seconds'
        ]
        read_only_fields = [
            'id', 'created_at', 'questions_generated', 'generation_successful',
            'error_message', 'generation_time_seconds'
        ]


class S3LibraryMCQRequestSerializer(serializers.Serializer):
    s3_key = serializers.CharField(max_length=1024)
    num_questions = serializers.IntegerField(min_value=1, max_value=50, default=10)
    generation_type = serializers.ChoiceField(
        choices=['full_book_wise', 'chapter_wise'],
        default='full_book_wise'
    )
    filename = serializers.CharField(max_length=255, required=False)