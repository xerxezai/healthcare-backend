from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
import json
import logging
from .serializers import (
    FileUploadSerializer, AnonymizeResponseSerializer,
    ReportAnalysisRequestSerializer, ReportAnalysisResponseSerializer,
    ProcessedDocumentSerializer
)
from .serializers import MultimodalQueryRequestSerializer, MultimodalQueryResponseSerializer
from .services.file_parser_service import parse_file_content
from .services.ai_service import get_radiology_ai_service
from .models import ProcessedDocument
import logging

logger = logging.getLogger(__name__)

class AnonymizeDocumentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_serializer = FileUploadSerializer(data=request.data)
        if not file_serializer.is_valid():
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = file_serializer.validated_data['file']
        
        processed_doc_record = ProcessedDocument.objects.create(
            user=request.user,
            original_filename=uploaded_file.name,
            processing_type='anonymization',
            status='pending'
        )

        try:
            text_content = parse_file_content(uploaded_file, uploaded_file.name)
            processed_doc_record.input_preview = text_content[:500]
        except ValueError as e:
            logger.error(f"File parsing error for anonymization: {e}")
            processed_doc_record.status = 'failed'
            processed_doc_record.save()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected file processing error for anonymization: {e}")
            processed_doc_record.status = 'failed'
            processed_doc_record.save()
            return Response({"error": "An unexpected error occurred while processing the file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        anonymized_text, redaction_summary, error = get_radiology_ai_service().anonymize_document_text(text_content)

        if error:
            logger.error(f"Anonymization AI error: {error}")
            processed_doc_record.status = 'failed'
            processed_doc_record.output_preview = error[:500]
            processed_doc_record.save()
            if anonymized_text:
                 response_data = {
                    "original_filename": uploaded_file.name,
                    "anonymized_text": anonymized_text,
                    "redaction_summary": redaction_summary or {},
                    "message": f"Anonymization partially successful with warning: {error}"
                }
                 return Response(AnonymizeResponseSerializer(response_data).data, status=status.HTTP_207_MULTI_STATUS)
            return Response({"error": f"Anonymization failed: {error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        processed_doc_record.status = 'completed'
        processed_doc_record.redacted_item_counts = redaction_summary
        processed_doc_record.output_preview = anonymized_text[:500]
        processed_doc_record.save()

        response_data = {
            "original_filename": uploaded_file.name,
            "anonymized_text": anonymized_text,
            "redaction_summary": redaction_summary
        }
        return Response(AnonymizeResponseSerializer(response_data).data, status=status.HTTP_200_OK)


class RadiologyMultimodalQueryView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = MultimodalQueryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"MultimodalQueryRequestSerializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        image_file = validated_data.get('image')
        user_query = validated_data['query']
        report_context_snippet = validated_data.get('report_context_snippet', '')
        
        conversation_history_json_str = validated_data.get('conversation_history_json', '[]')
        conversation_history = []
        try:
            parsed_history = json.loads(conversation_history_json_str)
            if isinstance(parsed_history, list):
                conversation_history = parsed_history
            else:
                logger.warning("conversation_history_json was not a list after parsing.")
        except json.JSONDecodeError:
            logger.warning("Failed to parse conversation_history_json string.")
        
        ai_response, error = get_radiology_ai_service().query_image_with_text(
            image_file_obj=image_file,
            text_query=user_query,
            report_context=report_context_snippet,
            conversation_history=conversation_history
        )

        if error:
            logger.error(f"Multimodal AI query error for user {request.user.email}: {error}")
            return Response({"error": f"AI query failed: {error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = {
            "ai_response": ai_response,
            "query_received": user_query,
            "image_processed_filename": image_file.name if image_file else None
        }
        return Response(MultimodalQueryResponseSerializer(response_data).data, status=status.HTTP_200_OK)
    
class AnalyzeReportView(APIView):
    # permission_classes = [IsAuthenticated]  # Temporarily disabled for testing
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        print(f"DEBUG: AnalyzeReportView received request")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request data: {request.data}")
        
        serializer = ReportAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            print(f"DEBUG: Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        text_content = serializer.validated_data.get('text_content')
        uploaded_file = serializer.validated_data.get('file')
        original_filename = None

        processed_doc_record = ProcessedDocument.objects.create(
            user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
            processing_type='report_analysis',
            status='pending'
        )

        if uploaded_file:
            original_filename = uploaded_file.name
            processed_doc_record.original_filename = original_filename
            try:
                text_content = parse_file_content(uploaded_file, uploaded_file.name)
            except ValueError as e:
                logger.error(f"File parsing error for report analysis: {e}")
                processed_doc_record.status = 'failed'; processed_doc_record.save()
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected file processing error for report analysis: {e}")
                processed_doc_record.status = 'failed'; processed_doc_record.save()
                return Response({"error": "An unexpected error occurred while processing the file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if not text_content or not text_content.strip():
            processed_doc_record.status = 'failed'; processed_doc_record.save()
            return Response({"error": "No text content to analyze."}, status=status.HTTP_400_BAD_REQUEST)

        processed_doc_record.input_preview = text_content[:500]
        
        analysis_result, error = get_radiology_ai_service().analyze_radiology_report(text_content)

        if error and not analysis_result:
            logger.error(f"Report analysis AI error: {error}")
            processed_doc_record.status = 'failed'
            processed_doc_record.output_preview = error[:500]
            processed_doc_record.save()
            return Response({"error": f"Report analysis failed: {error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if error and analysis_result:
             logger.warning(f"Report analysis AI partial error: {error}. Result: {analysis_result}")
        
        final_result = {
            "original_text": analysis_result.get("original_text", text_content),
            "flagged_issues": analysis_result.get("flagged_issues", []),
            "accuracy_score": analysis_result.get("accuracy_score", 0.0),
            "error_distribution": analysis_result.get("error_distribution", {}),
            "original_filename": original_filename,
            "message": f"Report analyzed { 'with warnings: ' + analysis_result.get('parsing_error', '') if analysis_result.get('parsing_error') else 'successfully.'}"
        }
        
        processed_doc_record.status = 'completed' if not analysis_result.get('parsing_error') else 'failed'
        processed_doc_record.accuracy_score = final_result["accuracy_score"]
        processed_doc_record.error_distribution = final_result["error_distribution"]
        summary = f"Accuracy: {final_result['accuracy_score']}%. Errors: {sum(final_result['error_distribution'].values())}."
        processed_doc_record.output_preview = summary[:500]
        processed_doc_record.save()

        return Response(ReportAnalysisResponseSerializer(final_result).data, status=status.HTTP_200_OK)


class ReportHistoryListView(generics.ListAPIView):
    serializer_class = ProcessedDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProcessedDocument.objects.filter(user=self.request.user).order_by('-created_at')


class AdvancedReportCorrectionView(APIView):
    """Advanced AI-powered report correction with RAG integration"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            report_text = request.data.get('report_text', '').strip()
            options = request.data.get('options', {})
            
            if not report_text:
                return Response({
                    'success': False,
                    'error': 'Report text is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Import the advanced processor
            from .services.advanced_report_ai import AdvancedReportProcessor
            
            processor = AdvancedReportProcessor()
            result = processor.process_report(report_text, options)
            
            # Save to processing history
            ProcessedDocument.objects.create(
                user=request.user,
                original_filename=f"report_correction_{result['timestamp']}.txt",
                processing_type='advanced_correction',
                status='completed',
                input_preview=report_text[:500],
                output_preview=result['corrected'][:500],
                accuracy_score=result['confidence'] * 100
            )
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Advanced report correction error: {e}")
            return Response({
                'success': False,
                'error': 'An error occurred during report correction'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdvancedConfigurationView(APIView):
    """Get advanced report correction configuration"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            from .services.advanced_report_ai import AdvancedReportProcessor
            
            processor = AdvancedReportProcessor()
            config = processor.get_configuration()
            
            return Response({
                'success': True,
                'data': config
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Configuration retrieval error: {e}")
            return Response({
                'success': False,
                'error': 'Could not retrieve configuration'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessingHistoryView(APIView):
    """Manage processing history for advanced report corrections"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Get last 50 advanced correction records
            history = ProcessedDocument.objects.filter(
                user=request.user,
                processing_type='advanced_correction'
            ).order_by('-created_at')[:50]
            
            history_data = []
            for record in history:
                history_data.append({
                    'id': record.id,
                    'timestamp': record.created_at.isoformat(),
                    'originalText': record.input_preview,
                    'correctedText': record.output_preview,
                    'confidence': record.accuracy_score / 100 if record.accuracy_score else 0.85,
                    'model': 'Advanced AI',
                    'processingTime': 2.5  # Default value
                })
            
            return Response({
                'success': True,
                'data': history_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"History retrieval error: {e}")
            return Response({
                'success': False,
                'error': 'Could not retrieve processing history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        try:
            # Save a new history entry
            history_entry = request.data
            
            ProcessedDocument.objects.create(
                user=request.user,
                original_filename=f"report_correction_{history_entry.get('timestamp', 'unknown')}.txt",
                processing_type='advanced_correction',
                status='completed',
                input_preview=history_entry.get('originalText', '')[:500],
                output_preview=history_entry.get('correctedText', '')[:500],
                accuracy_score=(history_entry.get('confidence', 0.85) * 100)
            )
            
            return Response({
                'success': True,
                'message': 'History entry saved successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"History save error: {e}")
            return Response({
                'success': False,
                'error': 'Could not save history entry'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdvancedAnalyzeReportView(APIView):
    """Advanced radiology report analysis with AI models, deep learning, and recommendations"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        try:
            # Extract basic data
            text_content = request.data.get('text_content')
            uploaded_file = request.data.get('file')
            image_file = request.data.get('image')
            
            # Extract advanced options
            ai_model = request.data.get('ai_model', 'ensemble')
            analysis_types = json.loads(request.data.get('analysis_types', '["anomalyDetection", "patternRecognition"]'))
            segmentation_methods = json.loads(request.data.get('segmentation_methods', '["semantic"]'))
            enable_recommendations = request.data.get('enable_recommendations', 'true').lower() == 'true'
            
            # Validate input
            if not text_content and not uploaded_file:
                return Response({
                    'error': 'Either text_content or file must be provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create processing record
            processed_doc_record = ProcessedDocument.objects.create(
                user=request.user,
                processing_type='advanced_analysis',
                status='pending'
            )
            
            # Parse file if provided
            original_filename = None
            if uploaded_file:
                original_filename = uploaded_file.name
                processed_doc_record.original_filename = original_filename
                try:
                    text_content = parse_file_content(uploaded_file, uploaded_file.name)
                except ValueError as e:
                    logger.error(f"File parsing error for advanced analysis: {e}")
                    processed_doc_record.status = 'failed'
                    processed_doc_record.save()
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    logger.error(f"Unexpected file processing error for advanced analysis: {e}")
                    processed_doc_record.status = 'failed'
                    processed_doc_record.save()
                    return Response({"error": "An unexpected error occurred while processing the file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            if not text_content or not text_content.strip():
                processed_doc_record.status = 'failed'
                processed_doc_record.save()
                return Response({"error": "No text content to analyze."}, status=status.HTTP_400_BAD_REQUEST)
            
            processed_doc_record.input_preview = text_content[:500]
            
            # Process image data if provided
            image_data = None
            if image_file:
                try:
                    image_data = image_file.read()
                except Exception as e:
                    logger.warning(f"Could not read image file: {e}")
            
            # Perform advanced analysis
            try:
                from .services.advanced_analyzer import advanced_analyzer
                
                options = {
                    'ai_model': ai_model,
                    'analysis_types': analysis_types,
                    'segmentation_methods': segmentation_methods,
                    'enable_recommendations': enable_recommendations
                }
                
                analysis_result = advanced_analyzer.analyze_report(
                    text_content, 
                    image_data, 
                    options
                )
                
                if 'error' in analysis_result:
                    processed_doc_record.status = 'failed'
                    processed_doc_record.output_preview = analysis_result['error'][:500]
                    processed_doc_record.save()
                    return Response({
                        "error": f"Advanced analysis failed: {analysis_result['error']}"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Update processing record
                processed_doc_record.status = 'completed'
                processed_doc_record.accuracy_score = analysis_result.get('accuracy_score', 0.0)
                processed_doc_record.output_preview = analysis_result.get('corrected_report_text', text_content)[:500]
                processed_doc_record.save()
                
                # Prepare response data
                response_data = {
                    'original_text': analysis_result.get('original_text', text_content),
                    'flagged_issues': analysis_result.get('flagged_issues', []),
                    'accuracy_score': analysis_result.get('accuracy_score', 0.0),
                    'corrected_report_text': analysis_result.get('corrected_report_text', ''),
                    'error_distribution': analysis_result.get('error_distribution', {}),
                    'original_filename': original_filename,
                    'message': f"Advanced analysis completed using {analysis_result.get('ai_model_used', 'AI')}",
                    
                    # Enhanced results
                    'deep_learning_results': analysis_result.get('deep_learning_results', {}),
                    'segmentation_results': analysis_result.get('segmentation_results', {}),
                    'recommendations': analysis_result.get('recommendations', {}),
                    'quality_metrics': analysis_result.get('quality_metrics', {}),
                    'ai_model_used': analysis_result.get('ai_model_used', 'Unknown'),
                    'processing_time': analysis_result.get('processing_time', 0),
                    'timestamp': analysis_result.get('timestamp', ''),
                    'analysis_types_used': analysis_types,
                    'segmentation_methods_used': segmentation_methods,
                    'recommendations_enabled': enable_recommendations
                }
                
                logger.info(f"Advanced analysis completed for user {request.user.id} using {ai_model}")
                return Response(response_data, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Advanced analysis error: {e}")
                processed_doc_record.status = 'failed'
                processed_doc_record.output_preview = str(e)[:500]
                processed_doc_record.save()
                return Response({
                    "error": "Advanced analysis service temporarily unavailable"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Advanced analysis request error: {e}")
            return Response({
                'error': 'An error occurred while processing your request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)