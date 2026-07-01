from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import logging
import time
import os
from django.conf import settings
from django.utils import timezone
import uuid

from .models import S3UploadedFile, S3LibraryBook, MCQGenerationHistory
from .serializers import (
    FileUploadSerializer, S3UploadedFileSerializer,
    DocumentProcessResponseSerializer
)
from .services.openai_service import openai_service
from .services.pdf_service import pdf_service
from .services.aws_s3_service import s3_service
from .services.s3_library_service import s3_library_service
from subscriptions.decorators import require_subscription, track_usage

logger = logging.getLogger(__name__)

class GenerateMCQView(views.APIView):
    """
    API endpoint to receive a file (PDF), extract text, and generate MCQs using AI.
    This view processes the file content directly and returns MCQs.
    It does NOT handle S3 upload; that is handled by DocumentUploadS3View.
    """
    permission_classes = [IsAuthenticated]
    
    parser_classes = [MultiPartParser, FormParser]

    @require_subscription(required_plans=['SecureNeat Basic', 'SecureNeat Pro'])
    @track_usage('Intelligent MCQ Generator')
    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        num_questions_str = request.data.get('num_questions')
        generation_type = request.data.get('generation_type', 'full_book_wise')

        if not uploaded_file:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        if not num_questions_str:
            return Response({"error": "Number of questions not provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            num_questions = int(num_questions_str)
            if not (1 <= num_questions <= 50):
                return Response({"error": "Number of questions must be between 1 and 50."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid number of questions. Must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        if generation_type not in ['full_book_wise', 'chapter_wise']:
            return Response({"error": "Invalid generation_type. Must be 'full_book_wise' or 'chapter_wise'."}, status=status.HTTP_400_BAD_REQUEST)

        
        if not uploaded_file.name.lower().endswith('.pdf'):
            return Response({"error": "Invalid file type. Only PDF is allowed for MCQ generation."}, status=status.HTTP_400_BAD_REQUEST)

        
        MAX_FILE_SIZE = 20 * 1024 * 1024 
        if uploaded_file.size > MAX_FILE_SIZE:
            return Response({"error": f"File is too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            uploaded_file.seek(0)
            pdf_content_buffer = uploaded_file.read()

            
            extracted_text = pdf_service.extract_text_from_pdf_buffer(pdf_content_buffer)

            if not extracted_text or len(extracted_text.strip()) < 50:
                 return Response({"error": "Could not extract sufficient text from the PDF or PDF content is too short."}, status=status.HTTP_400_BAD_REQUEST)

            
            topic_title_hint = uploaded_file.name[:-4] if uploaded_file.name.lower().endswith('.pdf') else "Uploaded Document"

            logger.info(f"Attempting to generate {num_questions} MCQs ({generation_type}) for file: {uploaded_file.name}, text length: {len(extracted_text)}")

            mcq_json, error = openai_service.generate_mcqs_from_text(
                extracted_text,
                num_questions,
                topic_title_hint,
                generation_type
            )

            if error:
                logger.error(f"MCQ generation failed for {uploaded_file.name}: {error}")
                return Response({"error": f"Failed to generate MCQs: {error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if not mcq_json:
                logger.error(f"MCQ generation returned no JSON for {uploaded_file.name}")
                return Response({"error": "MCQ generation failed to produce valid output."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            return Response(mcq_json, status=status.HTTP_200_OK)

        except ValueError as e: 
            logger.error(f"Error processing PDF {uploaded_file.name}: {e}")
            return Response({"error": f"Error processing PDF: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during MCQ generation for {uploaded_file.name}: {e}", exc_info=True)
            return Response({"error": "An unexpected error occurred while generating MCQs."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentUploadS3View(views.APIView):
    """
    API endpoint to request a presigned URL for direct S3 upload from the client.
    Accepts file metadata (filename, content_type, size) via JSON body.
    Creates a database record for the file *before* the client uploads it to S3.
    """
    permission_classes = [IsAuthenticated]
    
    parser_classes = [JSONParser]

    def post(self, request):
        
        filename = request.data.get('filename')
        content_type = request.data.get('content_type')
        

        if not filename or not content_type:
            return Response({"error": "filename and content_type are required."}, status=status.HTTP_400_BAD_REQUEST)

        
        
        allowed_extensions = ('.pdf', '.txt', '.doc', '.docx') 
        if not filename.lower().endswith(allowed_extensions):
             return Response({"error": f"Unsupported file extension. Allowed: {', '.join(allowed_extensions)}"}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.user.username

        
        presigned_post_data, object_key, error = s3_service.generate_presigned_post(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            expires_in=3600 
        )

        if error:
            logger.error(f"Failed to generate presigned URL for {filename} by user {user_id}: {error}")
            return Response({"error": "Failed to get S3 upload credentials", "details": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        
        try:
            s3_file_record = S3UploadedFile.objects.create(
                user=request.user,
                file_key=object_key,
                bucket_name=settings.AWS_STORAGE_BUCKET_NAME,
                original_filename=filename,
                content_type=content_type,
                
                
                file_url=f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{object_key}"
                
            )
            logger.info(f"DB record created for pending S3 upload: key={object_key}, DB ID={s3_file_record.id}")
        except Exception as e:
             logger.error(f"Failed to create DB record for S3 upload {object_key}: {e}")
             
             return Response({"error": "Failed to record file details in database."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        
        return Response({
            "success": True,
            "presigned_post": presigned_post_data, 
            "file_key": object_key,              
            "db_id": s3_file_record.id,          
            "file_url": s3_file_record.file_url  
        }, status=status.HTTP_200_OK) 


class DocumentProcessView(views.APIView):
    """
    API endpoint to receive a file, extract text, and perform AI analysis/summary.
    This view *does not* upload the file to S3.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @require_subscription(required_service='Data Anonymization Tool')
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Document process validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data['file']

        
        uploaded_file.seek(0)
        file_buffer = uploaded_file.read()

        extracted_text = ""
        try:
            if uploaded_file.content_type == 'application/pdf':
                extracted_text = pdf_service.extract_text_from_pdf_buffer(file_buffer)
            elif uploaded_file.content_type.startswith('text/'):
                extracted_text = file_buffer.decode('utf-8')
            else:
                logger.warning(f"Unsupported file type for processing: {uploaded_file.content_type}")
                return Response({"error": "Unsupported file type. Please upload PDF or TXT."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            logger.error(f"Text extraction error for user {request.user.id}, file {uploaded_file.name}: {e}")
            return Response({"error": "File processing failed during text extraction.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected text extraction error for user {request.user.id}, file {uploaded_file.name}: {e}")
            return Response({"error": "File processing failed.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        cleaned_text = ' '.join(extracted_text.split()).encode('ascii', 'ignore').decode('ascii')
        content_to_analyze = cleaned_text[:15000] 

        
        analysis, analysis_error = openai_service.analyze_medical_document(content_to_analyze)
        if analysis_error:
            logger.error(f"AI analysis failed for user {request.user.id}, file {uploaded_file.name}: {analysis_error}")
            return Response({"error": "Failed to analyze document with AI.", "details": analysis_error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        summary = openai_service.summarize_analysis(analysis)

        response_data = {
            "success": True,
            "summary": summary,
            
            "extracted_text_snippet": cleaned_text[:500] + "..." if len(cleaned_text) > 500 else cleaned_text
        }

        return Response(response_data, status=status.HTTP_200_OK)


# ===== S3 LIBRARY VIEWS =====

class S3LibraryCategoriesView(views.APIView):
    """
    Lists all available book categories in the S3 library.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            categories = s3_library_service.list_book_categories()
            return Response({
                "success": True,
                "categories": categories
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error listing S3 library categories: {e}")
            return Response({
                "error": "Failed to load library categories"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class S3LibraryBooksView(views.APIView):
    """
    Lists books in a specific category or searches across categories.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        category = request.query_params.get('category')
        subcategory = request.query_params.get('subcategory')
        search = request.query_params.get('search')
        
        try:
            if search:
                # Search across categories
                search_categories = request.query_params.getlist('categories') if request.query_params.get('categories') else None
                books = s3_library_service.search_books(search, search_categories)
            elif category:
                # List books in specific category
                books = s3_library_service.list_books_in_category(category, subcategory)
            else:
                # List all books (limit for performance)
                books = []
                categories = s3_library_service.list_book_categories()
                for cat in categories[:3]:  # Limit to first 3 categories
                    cat_books = s3_library_service.list_books_in_category(cat['key'])
                    books.extend(cat_books[:10])  # Limit to 10 books per category
            
            return Response({
                "success": True,
                "books": books,
                "count": len(books)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error listing S3 library books: {e}")
            return Response({
                "error": "Failed to load library books"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class S3LibraryMCQGenerateView(views.APIView):
    """
    Generate MCQs from books stored in S3 library.
    Enhanced version of GenerateMCQView that works with S3 library.
    """
    permission_classes = [IsAuthenticated]
    
    @require_subscription(required_plans=['SecureNeat Basic', 'SecureNeat Pro'])
    @track_usage('S3 Library MCQ Generator')
    def post(self, request, *args, **kwargs):
        s3_key = request.data.get('s3_key')
        num_questions = request.data.get('num_questions', 5)
        generation_type = request.data.get('generation_type', 'full_book_wise')
        
        if not s3_key:
            return Response({
                "error": "s3_key is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate parameters
        try:
            num_questions = int(num_questions)
            if not (1 <= num_questions <= 50):
                raise ValueError("Number of questions must be between 1 and 50")
        except (ValueError, TypeError):
            return Response({
                "error": "Invalid number of questions"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if generation_type not in ['full_book_wise', 'chapter_wise']:
            return Response({
                "error": "Invalid generation type"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Start timing
        import time
        start_time = time.time()
        
        # Initialize history record
        filename = os.path.basename(s3_key)
        history = MCQGenerationHistory.objects.create(
            user=request.user,
            s3_key=s3_key,
            filename=filename,
            num_questions=num_questions,
            generation_type=generation_type
        )
        
        try:
            # Download file content from S3
            file_content, error = s3_library_service.get_book_content(s3_key)
            if error:
                history.error_message = f"Failed to download file: {error}"
                history.save()
                return Response({
                    "error": "Failed to access book from library",
                    "details": error
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Extract text from PDF
            if filename.lower().endswith('.pdf'):
                try:
                    from io import BytesIO
                    pdf_buffer = BytesIO(file_content)
                    extracted_text = pdf_service.extract_text_from_pdf_buffer(pdf_buffer)
                except Exception as e:
                    history.error_message = f"PDF processing failed: {str(e)}"
                    history.save()
                    return Response({
                        "error": "Failed to process PDF file",
                        "details": str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # For text files, decode content
                try:
                    extracted_text = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        extracted_text = file_content.decode('latin1')
                    except Exception as e:
                        history.error_message = f"Text extraction failed: {str(e)}"
                        history.save()
                        return Response({
                            "error": "Failed to extract text from file",
                            "details": str(e)
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate extracted text
            if len(extracted_text.strip()) < 100:
                history.error_message = "Insufficient text content for MCQ generation"
                history.save()
                return Response({
                    "error": "Insufficient text content for MCQ generation"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate MCQs using OpenAI
            topic_title_hint = os.path.splitext(filename)[0]
            mcq_json, error = openai_service.generate_mcqs_from_text(
                extracted_text,
                num_questions,
                topic_title_hint,
                generation_type
            )
            
            if error:
                history.error_message = f"AI generation failed: {error}"
                history.save()
                return Response({
                    "error": "Failed to generate MCQs",
                    "details": error
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Calculate generation time
            generation_time = time.time() - start_time
            
            # Count generated questions
            if generation_type == 'chapter_wise':
                questions_count = sum(len(chapter.get('questions', [])) for chapter in mcq_json.get('chapters', []))
            else:
                questions_count = len(mcq_json.get('questions', []))
            
            # Update history
            history.questions_generated = questions_count
            history.generation_successful = True
            history.generation_time_seconds = generation_time
            history.save()
            
            # Update library book access tracking if exists
            try:
                library_book = S3LibraryBook.objects.get(s3_key=s3_key)
                library_book.mcq_generation_count += 1
                library_book.last_mcq_generated = timezone.now()
                library_book.save()
                history.library_book = library_book
                history.save()
            except S3LibraryBook.DoesNotExist:
                pass  # Book not in library database
            
            # Add metadata to response
            response_data = mcq_json.copy()
            response_data.update({
                "success": True,
                "source_file": filename,
                "s3_key": s3_key,
                "generation_type": generation_type,
                "questions_generated": questions_count,
                "generation_time": round(generation_time, 2),
                "history_id": history.id
            })
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Update history with error
            history.error_message = f"Unexpected error: {str(e)}"
            history.generation_time_seconds = time.time() - start_time
            history.save()
            
            logger.error(f"S3 Library MCQ generation failed for user {request.user.id}: {e}")
            return Response({
                "error": "MCQ generation failed",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class S3LibraryUploadView(views.APIView):
    """
    Upload new books to the S3 library with proper categorization.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        file_obj = request.FILES.get('file')
        category = request.data.get('category', 'medical_books')
        subcategory = request.data.get('subcategory')
        title = request.data.get('title')
        author = request.data.get('author')
        description = request.data.get('description')
        tags = request.data.get('tags')
        
        if not file_obj:
            return Response({
                "error": "File is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_extensions = ('.pdf', '.txt', '.doc', '.docx')
        if not file_obj.name.lower().endswith(allowed_extensions):
            return Response({
                "error": f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Upload to S3 library
            s3_key, error = s3_library_service.upload_book_to_library(
                file_obj, file_obj.name, category, subcategory
            )
            
            if error:
                return Response({
                    "error": "Failed to upload to library",
                    "details": error
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Create library book record
            library_book = S3LibraryBook.objects.create(
                title=title or os.path.splitext(file_obj.name)[0],
                s3_key=s3_key,
                category=category,
                subcategory=subcategory,
                filename=file_obj.name,
                file_size=file_obj.size,
                content_type=file_obj.content_type,
                author=author,
                description=description,
                tags=tags,
                added_by=request.user
            )
            
            return Response({
                "success": True,
                "message": "Book uploaded successfully",
                "book": {
                    "id": library_book.id,
                    "title": library_book.title,
                    "s3_key": s3_key,
                    "category": category,
                    "subcategory": subcategory,
                    "filename": file_obj.name,
                    "size_mb": library_book.size_mb
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error uploading book to library: {e}")
            return Response({
                "error": "Failed to upload book",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(DocumentProcessResponseSerializer(response_data).data, status=status.HTTP_200_OK)