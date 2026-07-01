import openai
from django.conf import settings
import base64
from io import BytesIO
from PIL import Image
import logging
import json

logger = logging.getLogger(__name__)

class RadiologyAIService:
    def __init__(self):
        try:
            openai_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not openai_key or openai_key == "emergency-placeholder-key":
                logger.warning("OPENAI_API_KEY not set or in emergency mode. Radiology AI services will not be available.")
                self.client = None
            else:
                try:
                    self.client = openai.OpenAI(api_key=openai_key)
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
                    self.client = None
        except Exception as e:
            logger.warning(f"Settings access error during AI service init: {e}")
            self.client = None

    def _make_chat_completion_request(self, messages, model="gpt-3.5-turbo", max_tokens=1500, temperature=0.5, response_format=None):
        if not self.client:
            return None, "OpenAI API key not configured."
        try:
            params = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if response_format:
                 params["response_format"] = response_format

            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content
            return content.strip(), None
        except openai.APIError as e:
            logger.error(f"OpenAI API Error: {e}")
            error_message = f"OpenAI API error: {e.status_code} - {getattr(e, 'message', str(e))}"
            if hasattr(e, 'body') and e.body and 'message' in e.body:
                 error_message = f"OpenAI API error: {e.status_code} - {e.body['message']}"
            return None, error_message
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}")
            return None, f"An unexpected error occurred with AI service: {str(e)}"

    def anonymize_document_text(self, text_content):
        system_prompt = """
You are an expert data anonymization tool. Analyze the following text and redact all Personally Identifiable Information (PII).
Replace PII with placeholders like [PATIENT_NAME], [DATE], [DOCTOR_NAME], [CONTACT_NUMBER], [MEDICAL_RECORD_ID], [ADDRESS], [AGE], [HOSPITAL_NAME], [LOCATION], etc.
Provide the anonymized text. Also, provide a JSON summary of the count of each type of PII redacted.
PII categories to consider:
- Patient Names (and initials if clearly identifying)
- Doctor Names (and other healthcare provider names)
- Dates (All specific dates like Birth, Admission, Discharge, Procedure, Report dates)
- Contact Information (Phone numbers, Email addresses, Fax numbers)
- Addresses (Street addresses, City, State, ZIP codes if specific and identifying)
- Medical Record Numbers (MRN), Patient IDs, Account Numbers
- Social Security Numbers (or equivalents)
- Vehicle Identifiers, Device Serial Numbers
- Biometric Identifiers
- Full face photographic images (description if text refers to one)
- Any other unique identifying number, characteristic, or code (e.g., Accession Numbers, Study IDs if they are unique and traceable)
- Ages over 89 or specific ages if contextually identifying. Replace with [AGE_OVER_89] or [AGE].
- Names of relatives if identifying.
- Geographic subdivisions smaller than a state, including street address, city, county, precinct, zip code, and their equivalent geocodes, except for the initial three digits of a zip code if certain conditions are met (for simplicity, aim to redact specific locations).
Output format MUST be a JSON object with two keys:
1.  "anonymized_text": "The full anonymized text content."
2.  "redaction_summary": A JSON object detailing counts, e.g., {"Patient Names": 2, "Dates": 3, "Contact Information": 1}
Example of redaction_summary: {"Patient Names": 1, "Dates": 2, "Medical Record IDs": 1}
If no PII of a certain type is found, do not include it in the summary or set its count to 0.
"""
        user_prompt = f"Anonymize the following text:\n\n---\n{text_content}\n---"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        raw_response, error = self._make_chat_completion_request(
            messages, 
            model="gpt-3.5-turbo-0125", 
            max_tokens=2000, 
            temperature=0.2,
            response_format={ "type": "json_object" }
        )

        if error:
            return None, None, error
        
        if not raw_response:
            return None, None, "AI service returned an empty response."

        try:
            parsed_json = json.loads(raw_response)
            anonymized_text = parsed_json.get("anonymized_text")
            redaction_summary = parsed_json.get("redaction_summary", {})
            if not anonymized_text:
                return None, None, "AI response missing 'anonymized_text'."
            return anonymized_text, redaction_summary, None
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from anonymization AI response: {raw_response[:500]}")
            return raw_response, {}, "AI response was not valid JSON, but text was returned."
        except Exception as e:
            logger.error(f"Error processing AI response for anonymization: {e}")
            return None, None, str(e)

    def analyze_radiology_report(self, report_text):
        # If OpenAI client is not available, use simulation mode
        if not self.client:
            return self._simulate_radiology_analysis(report_text), None
            
        system_prompt = """
You are an AI medical report analyzer specializing in radiology. Analyze the provided radiology report text for potential errors.
The user will provide a block of text. You MUST return this exact block of text as the 'original_text' field in your JSON response.
For each identified issue, provide:
1.  `type`: The type of error (e.g., 'Factual Inconsistency', 'Typographical Error', 'Misspelled Terminology', 'Unit Inconsistency', 'Potential Misdiagnosis', 'Grammar/Syntax', 'Omission', 'Clarity Issue').
2.  `description`: A brief description of the issue.
3.  `segment`: The EXACT problematic text segment from the 'original_text'. This MUST be an exact substring from the original report. For example, if the original text has "The patient has feever.", the segment should be "feever". If the error is "100 mg should be 10 mg", the segment is "100 mg".
4.  `suggestion`: A suggested correction or clarification for the 'segment'.
Also, provide an overall `accuracy_score` for the report (0-100), where 100 is perfectly accurate and error-free.
Finally, provide an `error_distribution` as a dictionary of error types and their counts (e.g., {"Typographical Error": 2, "Clarity Issue": 1}).
Output format MUST be a JSON object with the following keys:
- `original_text`: The original report text exactly as provided by the user for analysis.
- `flagged_issues`: An array of objects, each representing an issue with 'type', 'description', 'segment', and 'suggestion'. If no issues, this should be an empty array.
- `accuracy_score`: A float between 0 and 100.
- `error_distribution`: A dictionary summarizing error counts by type.
Example of a flagged issue:
{
  "type": "Typographical Error",
  "description": "Misspelling of 'fever'.",
  "segment": "feever",
  "suggestion": "fever"
}
It is CRITICAL that the 'segment' is the precise text from the original document that contains the error. Do NOT include startIndex or endIndex.
"""
        user_prompt = f"Analyze this radiology report:\n\n---\n{report_text}\n---"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        raw_response, error = self._make_chat_completion_request(
            messages,
            model="gpt-4-turbo", 
            max_tokens=3500, 
            temperature=0.15,
            response_format={ "type": "json_object" }
        )

        if error:
            return None, error
        
        if not raw_response:
            return None, "AI service returned an empty response for report analysis."

        try:
            analysis_result = json.loads(raw_response)
            
            if "original_text" not in analysis_result or not analysis_result.get("original_text"):
                logger.warning("LLM did not return 'original_text'. Using input report_text instead.")
                analysis_result["original_text"] = report_text

            if not all(k in analysis_result for k in ['flagged_issues', 'accuracy_score', 'error_distribution']):
                logger.error(f"Report analysis AI response missing some required keys: {raw_response[:500]}")
                analysis_result.setdefault('flagged_issues', [])
                analysis_result.setdefault('accuracy_score', 0.0)
                analysis_result.setdefault('error_distribution', {})
                return analysis_result, "AI response structure is incomplete."

            processed_issues = []
            for issue_idx, issue in enumerate(analysis_result.get("flagged_issues", [])):
                required_keys = ['type', 'description', 'segment', 'suggestion']
                if not all(k_issue in issue for k_issue in required_keys):
                    logger.warning(f"A flagged issue (index {issue_idx}) is missing one or more required keys ({', '.join(required_keys)}): {issue}")
                    continue 
                
                segment_value = issue.get('segment')
                if not isinstance(segment_value, str) or not segment_value.strip():
                    logger.warning(f"A flagged issue (index {issue_idx}) has an invalid or empty segment: {issue}")
                    continue
                
                issue.pop('startIndex', None)
                issue.pop('endIndex', None)
                
                processed_issues.append(issue)
            analysis_result['flagged_issues'] = processed_issues
            
            return analysis_result, None
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from report analysis AI response: {raw_response[:500]}")
            return {
                "original_text": report_text, 
                "flagged_issues": [], 
                "accuracy_score": 0, 
                "error_distribution": {}, 
                "parsing_error": "AI response was not valid JSON."
            }, "Failed to parse AI response."
        except Exception as e:
            logger.error(f"Error processing AI response for report analysis: {e}")
            return None, str(e)
    
    def _prepare_image_for_openai(self, image_file_obj):
        if image_file_obj is None:
            return None, None
        try:
            image_file_obj.seek(0)
            img = Image.open(image_file_obj)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{img_base64}", None
        except Exception as e:
            logger.error(f"Error preparing image for OpenAI: {e}")
            return None, f"Error processing image: {str(e)}"

    def query_image_with_text(self, image_file_obj, text_query: str, report_context: str = "", conversation_history: list = None):
        if not self.client:
            return None, "OpenAI API key not configured."

        base64_image_url, image_error = self._prepare_image_for_openai(image_file_obj)
        if image_error: 
            if image_file_obj is not None:
                return None, image_error
        
        system_prompt_parts = ["You are an expert radiology assistant."]
        if base64_image_url and report_context:
            system_prompt_parts.append("Analyze the provided chest X-ray image in conjunction with the user's query, the provided report context, and conversation history.")
        elif base64_image_url:
            system_prompt_parts.append("Analyze the provided chest X-ray image in conjunction with the user's query and conversation history.")
            system_prompt_parts.append("If the user asks 'what is in this image?' or similar, describe the image's content from a radiological perspective.")
        elif report_context:
            system_prompt_parts.append("Analyze the provided radiology report context in conjunction with the user's query and conversation history.")
        else:
            system_prompt_parts.append("Answer the user's query based on your general radiological knowledge and conversation history.")
        
        system_prompt_parts.append("Provide clear, concise, and medically accurate answers.")
        system_prompt_parts.append("If asked to localize findings (and an image is available), describe the location clearly (e.g., 'upper right lung zone', 'behind the heart').")
        
        system_prompt = " ".join(system_prompt_parts)
        
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            for msg in conversation_history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    content_str = msg["content"]
                    if not isinstance(content_str, str):
                        try:
                            content_str = json.dumps(content_str)
                        except TypeError:
                            content_str = str(content_str)
                    messages.append({"role": msg["role"], "content": content_str})
        
        user_message_content = []
        
        current_query_text = text_query
        if report_context:
            current_query_text += f"\n\nRelevant context from the radiology report:\n---\n{report_context}\n---"
        
        user_message_content.append({"type": "text", "text": current_query_text})

        if base64_image_url:
            user_message_content.append({
                "type": "image_url",
                "image_url": {"url": base64_image_url}
            })
        
        messages.append({"role": "user", "content": user_message_content})
        
        response_content, error = self._make_chat_completion_request(
            messages,
            model="gpt-4o", 
            max_tokens=1500, 
            temperature=0.3 
        )

        if error:
            return None, error
        
        return response_content, None

    def _simulate_radiology_analysis(self, report_text):
        """
        Simulation mode for radiology report analysis when OpenAI API is not available.
        Provides realistic medical analysis with common radiology terms and issues.
        """
        import re
        import random
        
        # Common medical terminology and potential issues
        common_typos = {
            'feever': 'fever',
            'pnemonia': 'pneumonia',
            'inflamation': 'inflammation',
            'broncial': 'bronchial',
            'cardio-vascular': 'cardiovascular',
            'abnormality': 'abnormality',
            'appearence': 'appearance',
            'comparision': 'comparison',
            'recomendation': 'recommendation',
            'consistant': 'consistent',
            'sugest': 'suggest',
            'definitly': 'definitely'
        }
        
        unit_patterns = {
            r'\b(\d+)\s*mm\b': 'millimeters',
            r'\b(\d+)\s*cm\b': 'centimeters', 
            r'\b(\d+)\s*mg\b': 'milligrams',
            r'\b(\d+)\s*ml\b': 'milliliters'
        }
        
        flagged_issues = []
        error_distribution = {}
        text_lower = report_text.lower()
        
        # Check for common typos
        for typo, correction in common_typos.items():
            if typo in text_lower:
                flagged_issues.append({
                    "type": "Typographical Error",
                    "description": f"Misspelling of '{correction}'",
                    "segment": typo,
                    "suggestion": correction
                })
                error_distribution["Typographical Error"] = error_distribution.get("Typographical Error", 0) + 1
        
        # Check for potential clarity issues
        if len(report_text.split('.')) > 10 and random.random() < 0.3:
            flagged_issues.append({
                "type": "Clarity Issue",
                "description": "Consider breaking down long sentences for better readability",
                "segment": report_text.split('.')[0] + '.',
                "suggestion": "Break into shorter sentences for clarity"
            })
            error_distribution["Clarity Issue"] = error_distribution.get("Clarity Issue", 0) + 1
        
        # Check for missing punctuation
        sentences = report_text.split('\n')
        for sentence in sentences:
            if sentence.strip() and not sentence.strip().endswith('.') and len(sentence) > 20:
                flagged_issues.append({
                    "type": "Grammar/Syntax",
                    "description": "Missing sentence termination",
                    "segment": sentence.strip()[-20:],
                    "suggestion": "Add proper punctuation at sentence end"
                })
                error_distribution["Grammar/Syntax"] = error_distribution.get("Grammar/Syntax", 0) + 1
                break
        
        # Add some medical-specific analysis
        medical_terms = ['chest', 'lung', 'heart', 'pneumonia', 'fracture', 'opacity', 'consolidation', 'effusion']
        found_terms = [term for term in medical_terms if term.lower() in text_lower]
        
        if 'chest' in text_lower and 'x-ray' in text_lower and random.random() < 0.4:
            flagged_issues.append({
                "type": "Recommendation",
                "description": "Consider follow-up imaging if symptoms persist",
                "segment": "chest x-ray",
                "suggestion": "Recommend follow-up CT if clinical symptoms warrant"
            })
            error_distribution["Recommendation"] = error_distribution.get("Recommendation", 0) + 1
        
        # Calculate accuracy score based on issues found
        total_words = len(report_text.split())
        issue_density = len(flagged_issues) / max(total_words / 10, 1)  # Issues per 10 words
        accuracy_score = max(60, min(95, 90 - (issue_density * 15)))
        
        # Add some randomness for realistic variation
        accuracy_score += random.uniform(-5, 5)
        accuracy_score = max(0, min(100, accuracy_score))
        
        return {
            "original_text": report_text,
            "flagged_issues": flagged_issues,
            "accuracy_score": round(accuracy_score, 1),
            "error_distribution": error_distribution,
            "simulation_mode": True,
            "message": "Analysis completed using simulation mode (OpenAI API not configured)"
        }

# Lazy initialization to avoid import-time errors
radiology_ai_service = None

def get_radiology_ai_service():
    global radiology_ai_service
    if radiology_ai_service is None:
        try:
            radiology_ai_service = RadiologyAIService()
        except Exception as e:
            logger.warning(f"Failed to initialize radiology AI service: {e}")
            radiology_ai_service = RadiologyAIService()  # Will create with null client
    return radiology_ai_service