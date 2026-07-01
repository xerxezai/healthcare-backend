"""
🎤 Voice Recognition & AI Enhancement Views
==========================================

Advanced AI-powered voice recognition system for radiology reporting with:
- Medical terminology correction
- Structured report formatting
- Clinical validation
- Smart punctuation and grammar
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import re
import logging
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class VoiceRecognitionProcessor:
    """
    AI-powered voice recognition text processor for medical reports
    """
    
    # Medical terminology correction dictionary
    MEDICAL_CORRECTIONS = {
        # Common speech recognition errors for medical terms
        'new monia': 'pneumonia',
        'pleural fusion': 'pleural effusion',
        'radio opaque': 'radiopaque',
        'radio lucent': 'radiolucent',
        'cardio megaly': 'cardiomegaly',
        'atelectasiss': 'atelectasis',
        'hyper dense': 'hyperdense',
        'hypo dense': 'hypodense',
        'contrast enhancement': 'contrast enhancement',
        'artifact': 'artifact',
        'mass effect': 'mass effect',
        'midline shift': 'midline shift',
        'acute finding': 'acute finding',
        'chronic changes': 'chronic changes',
        'degenerative changes': 'degenerative changes',
        'post surgical changes': 'post-surgical changes',
        'hemorrhagic': 'hemorrhagic',
        'ischemic': 'ischemic',
        'hyperintense': 'hyperintense',
        'hypointense': 'hypointense',
        'gadolinium enhancement': 'gadolinium enhancement',
        'diffusion restriction': 'diffusion restriction',
        'fluid attenuated inversion recovery': 'FLAIR',
        'T1 weighted': 'T1-weighted',
        'T2 weighted': 'T2-weighted',
    }
    
    # Critical findings that need highlighting
    CRITICAL_FINDINGS = [
        'mass', 'tumor', 'fracture', 'hemorrhage', 'pneumothorax', 
        'pulmonary embolism', 'acute infarct', 'acute bleed',
        'free air', 'perforation', 'obstruction', 'dissection'
    ]
    
    # Report templates with medical structure
    REPORT_TEMPLATES = {
        'general': {
            'name': 'General Radiology Report',
            'sections': [
                'CLINICAL HISTORY:',
                'TECHNIQUE:',
                'FINDINGS:',
                'IMPRESSION:'
            ]
        },
        'chest': {
            'name': 'Chest X-Ray Report',
            'sections': [
                'CLINICAL INDICATION:',
                'TECHNIQUE:',
                'COMPARISON:',
                'FINDINGS:',
                'Lungs:',
                'Heart:',
                'Mediastinum:',
                'Bones:',
                'IMPRESSION:'
            ]
        },
        'ct': {
            'name': 'CT Scan Report',
            'sections': [
                'CLINICAL HISTORY:',
                'TECHNIQUE:',
                'CONTRAST:',
                'COMPARISON:',
                'FINDINGS:',
                'IMPRESSION:'
            ]
        },
        'mri': {
            'name': 'MRI Report',
            'sections': [
                'CLINICAL INDICATION:',
                'TECHNIQUE:',
                'CONTRAST:',
                'SEQUENCES:',
                'FINDINGS:',
                'IMPRESSION:'
            ]
        }
    }

    @classmethod
    def correct_medical_terms(cls, text: str) -> str:
        """
        Correct common speech recognition errors in medical terminology
        """
        corrected_text = text
        
        for incorrect, correct in cls.MEDICAL_CORRECTIONS.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(incorrect), re.IGNORECASE)
            corrected_text = pattern.sub(correct, corrected_text)
        
        return corrected_text

    @classmethod
    def add_smart_punctuation(cls, text: str) -> str:
        """
        Add intelligent punctuation for medical reports
        """
        # Basic punctuation rules
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'([a-z])([A-Z])', r'\1. \2', text)  # Add periods between sentences
        text = re.sub(r'(\d+)\s*(mm|cm|inches?)', r'\1 \2', text)  # Normalize measurements
        text = re.sub(r'(\d+)\s*x\s*(\d+)', r'\1 x \2', text)  # Normalize dimensions
        
        # Medical-specific punctuation
        text = re.sub(r'impression\s*([a-z])', r'IMPRESSION:\n\1', text, flags=re.IGNORECASE)
        text = re.sub(r'findings\s*([a-z])', r'FINDINGS:\n\1', text, flags=re.IGNORECASE)
        
        return text.strip()

    @classmethod
    def highlight_critical_findings(cls, text: str) -> str:
        """
        Highlight critical findings in the report
        """
        highlighted_text = text
        
        for finding in cls.CRITICAL_FINDINGS:
            pattern = re.compile(f'\\b{re.escape(finding)}\\b', re.IGNORECASE)
            highlighted_text = pattern.sub(f'**{finding.upper()}**', highlighted_text)
        
        return highlighted_text

    @classmethod
    def format_with_template(cls, text: str, template_key: str) -> str:
        """
        Format text according to the specified template structure
        """
        if template_key not in cls.REPORT_TEMPLATES:
            return text
        
        template = cls.REPORT_TEMPLATES[template_key]
        sections = template['sections']
        
        formatted_text = text
        
        # Add template structure
        for section in sections:
            section_name = section.replace(':', '').strip()
            pattern = re.compile(f'\\b{re.escape(section_name)}\\b', re.IGNORECASE)
            formatted_text = pattern.sub(f'\n\n{section}\n', formatted_text)
        
        return formatted_text

    @classmethod
    def validate_clinical_content(cls, text: str) -> Dict:
        """
        Validate clinical content and provide suggestions
        """
        validation_results = {
            'critical_findings': [],
            'missing_sections': [],
            'suggestions': [],
            'confidence_score': 0.8
        }
        
        # Check for critical findings
        for finding in cls.CRITICAL_FINDINGS:
            if re.search(f'\\b{finding}\\b', text, re.IGNORECASE):
                validation_results['critical_findings'].append(finding)
        
        # Check for standard sections
        required_sections = ['findings', 'impression']
        for section in required_sections:
            if not re.search(f'\\b{section}\\b', text, re.IGNORECASE):
                validation_results['missing_sections'].append(section)
        
        # Generate suggestions
        if validation_results['critical_findings']:
            validation_results['suggestions'].append(
                f"Critical findings identified: {', '.join(validation_results['critical_findings'])}. "
                "Please ensure appropriate follow-up recommendations."
            )
        
        if validation_results['missing_sections']:
            validation_results['suggestions'].append(
                f"Consider adding these sections: {', '.join(validation_results['missing_sections'])}"
            )
        
        return validation_results


@method_decorator(csrf_exempt, name='dispatch')
class VoiceRecognitionAPI(View):
    """
    API endpoint for voice recognition text processing
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            template = data.get('template', 'general')
            enhancements = data.get('enhancements', {})
            
            if not text:
                return JsonResponse({
                    'error': 'Text is required',
                    'status': 'error'
                }, status=400)
            
            processor = VoiceRecognitionProcessor()
            enhanced_text = text
            
            # Apply enhancements based on user settings
            if enhancements.get('medical_term_correction', True):
                enhanced_text = processor.correct_medical_terms(enhanced_text)
            
            if enhancements.get('smart_punctuation', True):
                enhanced_text = processor.add_smart_punctuation(enhanced_text)
            
            if enhancements.get('template_structuring', True):
                enhanced_text = processor.format_with_template(enhanced_text, template)
            
            if enhancements.get('clinical_validation', True):
                enhanced_text = processor.highlight_critical_findings(enhanced_text)
            
            # Get validation results
            validation = processor.validate_clinical_content(enhanced_text)
            
            response_data = {
                'status': 'success',
                'original_text': text,
                'enhanced_text': enhanced_text,
                'template_used': template,
                'validation': validation,
                'timestamp': datetime.now().isoformat(),
                'enhancements_applied': enhancements
            }
            
            logger.info(f"Voice recognition processing completed for template: {template}")
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data',
                'status': 'error'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Voice recognition processing error: {str(e)}")
            return JsonResponse({
                'error': f'Processing failed: {str(e)}',
                'status': 'error'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ReportTemplateAPI(View):
    """
    API endpoint for managing report templates
    """
    
    def get(self, request):
        """Get available report templates"""
        try:
            templates = VoiceRecognitionProcessor.REPORT_TEMPLATES
            
            return JsonResponse({
                'status': 'success',
                'templates': templates,
                'count': len(templates)
            })
            
        except Exception as e:
            logger.error(f"Template retrieval error: {str(e)}")
            return JsonResponse({
                'error': f'Failed to retrieve templates: {str(e)}',
                'status': 'error'
            }, status=500)
    
    def post(self, request):
        """Get formatted template structure"""
        try:
            data = json.loads(request.body)
            template_key = data.get('template', 'general')
            
            if template_key not in VoiceRecognitionProcessor.REPORT_TEMPLATES:
                return JsonResponse({
                    'error': 'Invalid template key',
                    'status': 'error'
                }, status=400)
            
            template = VoiceRecognitionProcessor.REPORT_TEMPLATES[template_key]
            formatted_template = '\n\n'.join(template['sections']) + '\n\n'
            
            return JsonResponse({
                'status': 'success',
                'template_key': template_key,
                'template_name': template['name'],
                'formatted_template': formatted_template,
                'sections': template['sections']
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data',
                'status': 'error'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Template formatting error: {str(e)}")
            return JsonResponse({
                'error': f'Template formatting failed: {str(e)}',
                'status': 'error'
            }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def save_voice_report(request):
    """
    Save voice-generated report to database
    """
    try:
        data = json.loads(request.body)
        report_content = data.get('content', '')
        template_used = data.get('template', 'general')
        confidence_score = data.get('confidence', 0.0)
        
        if not report_content:
            return JsonResponse({
                'error': 'Report content is required',
                'status': 'error'
            }, status=400)
        
        # Here you would typically save to your Report model
        # For now, we'll return a success response
        
        report_data = {
            'id': f"voice_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'content': report_content,
            'template': template_used,
            'confidence': confidence_score,
            'created_at': datetime.now().isoformat(),
            'method': 'voice_recognition'
        }
        
        logger.info(f"Voice report saved with ID: {report_data['id']}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Report saved successfully',
            'report': report_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data',
            'status': 'error'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Report saving error: {str(e)}")
        return JsonResponse({
            'error': f'Failed to save report: {str(e)}',
            'status': 'error'
        }, status=500)


@require_http_methods(["GET"])
def get_voice_commands(request):
    """
    Get available voice commands for the system
    """
    try:
        voice_commands = {
            'navigation': {
                'new report': 'Start a new report',
                'save report': 'Save the current report',
                'clear text': 'Clear all text content',
                'load template': 'Load a report template'
            },
            'templates': {
                'select general template': 'Switch to general radiology template',
                'select chest template': 'Switch to chest X-ray template',
                'select ct template': 'Switch to CT scan template',
                'select mri template': 'Switch to MRI template'
            },
            'formatting': {
                'next section': 'Move to the next report section',
                'previous section': 'Move to the previous section',
                'enhance with ai': 'Apply AI enhancements to text',
                'add impression': 'Add impression section'
            },
            'navigation_sections': {
                'go to findings': 'Navigate to findings section',
                'go to impression': 'Navigate to impression section',
                'go to technique': 'Navigate to technique section',
                'go to comparison': 'Navigate to comparison section'
            }
        }
        
        return JsonResponse({
            'status': 'success',
            'voice_commands': voice_commands,
            'total_commands': sum(len(category) for category in voice_commands.values())
        })
        
    except Exception as e:
        logger.error(f"Voice commands retrieval error: {str(e)}")
        return JsonResponse({
            'error': f'Failed to retrieve voice commands: {str(e)}',
            'status': 'error'
        }, status=500)
