import openai
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set. OpenAI services will not be available.")
            self.client = None
        else:
            try:
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None

    def _make_chat_completion_request(self, messages, model="gpt-3.5-turbo", max_tokens=150, temperature=0.7, response_format=None):
        if not self.client:
            return "OpenAI API key not configured.", None
        try:
            params = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
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

    def generate_mcqs_from_text(self, text_content, num_questions, topic_title_hint="Generated MCQs", generation_type="full_book_wise"):
        if not self.client:
            logger.error("OpenAI client not initialized. Cannot generate MCQs.")
            return None, "OpenAI client not initialized."

        system_prompt = ""
        if generation_type == "chapter_wise":
            system_prompt = f"""
You are an expert MCQ generator specializing in medical and healthcare education. Your task is to analyze the provided text, identify distinct chapters, and then generate multiple-choice questions for each chapter.
The user desires approximately {num_questions} total questions distributed across these chapters.
The output MUST be a JSON object only, with the following structure:
{{
  "document_title": "<Topic Title - use the hint '{topic_title_hint}' or derive from content if more appropriate>",
  "mcq_type": "chapter_wise",
  "chapters": [
    {{
      "chapter_title": "<Identified Chapter Title>",
      "questions": [
        {{
          "question": "<Question text>",
          "options": ["<Option A>", "<Option B>", "<Option C>", "<Option D>"],
          "correct_answer": "<Correct Option index (0-indexed integer)>",
          "explanation": "<Comprehensive explanation for the correct answer - minimum 200 words covering pathophysiology, clinical significance, treatment implications, and why other options are incorrect>"
        }}
      ]
    }}
  ]
}}
Ensure each question has exactly four options. The 'correct_answer' field must be an integer index (0, 1, 2, or 3). 
CRITICAL: Each explanation must be at least 200 words and provide comprehensive educational value including:
- Detailed pathophysiology or mechanism
- Clinical significance and implications
- Why the correct answer is right
- Why the incorrect options are wrong
- Relevant treatment considerations or diagnostic approaches
- Learning points for medical/healthcare students

The number of questions per chapter can vary, but try to distribute the total questions meaningfully across the chapters based on their content and length, aiming for a total around {num_questions} questions.
If no clear chapters are identifiable, you may structure the output as a single chapter titled "Main Content" or similar.
"""
        else: # full_book_wise (default)
            system_prompt = f"""
You are an expert MCQ generator specializing in medical and healthcare education. Your task is to generate exactly {num_questions} multiple-choice questions based on the provided text.
The output MUST be a JSON object only, with the following structure:
{{
  "document_title": "<Topic Title - use the hint '{topic_title_hint}' or derive from content if more appropriate>",
  "mcq_type": "full_book_wise",
  "questions": [
    {{
      "question": "<Question text>",
      "options": ["<Option A>", "<Option B>", "<Option C>", "<Option D>"],
      "correct_answer": "<Correct Option index (0-indexed integer)>",
      "explanation": "<Comprehensive explanation for the correct answer - minimum 200 words covering pathophysiology, clinical significance, treatment implications, and why other options are incorrect>"
    }}
  ]
}}
Ensure each question has exactly four options. The 'correct_answer' field must be an integer index (0, 1, 2, or 3).
CRITICAL: Each explanation must be at least 200 words and provide comprehensive educational value including:
- Detailed pathophysiology or mechanism
- Clinical significance and implications  
- Why the correct answer is right
- Why the incorrect options are wrong
- Relevant treatment considerations or diagnostic approaches
- Learning points for medical/healthcare students

The number of question objects in the "questions" array must be exactly {num_questions}.
"""

        max_content_chars = 15000 
        if len(text_content) > max_content_chars:
            logger.warning(f"Input text content truncated from {len(text_content)} to {max_content_chars} characters for MCQ generation.")
        
        user_prompt = f"""
Please generate MCQs from the following text based on the generation type '{generation_type}':

--- TEXT START ---
{text_content[:max_content_chars]}
--- TEXT END ---

IMPORTANT REQUIREMENTS:
1. Each explanation must be at least 200 words
2. Provide comprehensive educational content in explanations
3. Include pathophysiology, clinical significance, and treatment considerations
4. Explain why incorrect options are wrong
5. Focus on medical/healthcare education best practices
6. Strictly follow the JSON output format
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        estimated_tokens_per_question = 500 # Significantly increased due to 200+ word explanations
        max_response_tokens = (num_questions * estimated_tokens_per_question) + 1000 # Increased buffer
        
        model_to_use = "gpt-3.5-turbo-0125" 
        if max_response_tokens > 4000: 
            max_response_tokens = 4000 # Max for gpt-3.5-turbo-0125 is 4096 for response
            logger.warning(f"Requested MCQs might exceed token limit. Capping response tokens at {max_response_tokens}.")
        
        # For longer explanations, use fewer questions if necessary to stay within limits
        if num_questions > 8 and max_response_tokens >= 4000:
            logger.warning(f"Large number of questions ({num_questions}) with detailed explanations may exceed token limits. Consider reducing question count for optimal results.")

        raw_response_content, error = self._make_chat_completion_request(
            messages,
            model=model_to_use,
            max_tokens=max_response_tokens,
            temperature=0.4, 
            response_format={ "type": "json_object" }
        )

        if error:
            return None, error
        
        if not raw_response_content:
            return None, "AI service returned an empty response."

        logger.debug(f"Raw OpenAI response for MCQ generation ({generation_type}): {raw_response_content[:500]}...")

        try:
            parsed_json = json.loads(raw_response_content)
            
            # Validate common fields
            if "document_title" not in parsed_json or "mcq_type" not in parsed_json:
                raise ValueError("Missing 'document_title' or 'mcq_type' in LLM response.")

            if parsed_json["mcq_type"] == "chapter_wise":
                if "chapters" not in parsed_json or not isinstance(parsed_json["chapters"], list):
                    raise ValueError("Missing 'chapters' list for chapter_wise MCQs.")
                for chap_idx, chapter in enumerate(parsed_json["chapters"]):
                    if "chapter_title" not in chapter or "questions" not in chapter or not isinstance(chapter["questions"], list):
                        raise ValueError(f"Chapter at index {chap_idx} is missing 'chapter_title' or 'questions' list.")
                    for q_idx, q_item in enumerate(chapter["questions"]):
                        self._validate_question_item(q_item, q_idx, chap_idx)
            elif parsed_json["mcq_type"] == "full_book_wise":
                if "questions" not in parsed_json or not isinstance(parsed_json["questions"], list):
                     raise ValueError("'questions' field is not a list for full_book_wise MCQs.")
                # if len(parsed_json["questions"]) != num_questions: # Relax this for now, AI might not always be exact
                #     logger.warning(f"LLM generated {len(parsed_json['questions'])} questions, but {num_questions} were requested for full book.")
                for q_idx, q_item in enumerate(parsed_json["questions"]):
                    self._validate_question_item(q_item, q_idx)
            else:
                raise ValueError(f"Unknown mcq_type: {parsed_json['mcq_type']}")

            return parsed_json, None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}. Response: {raw_response_content[:500]}...")
            return None, "Failed to parse AI response as JSON. The AI may not have followed the format strictly."
        except ValueError as e:
            logger.error(f"Invalid JSON structure from OpenAI: {e}. Response: {raw_response_content[:500]}...")
            return None, f"AI response has invalid structure: {str(e)}"

    def _validate_question_item(self, q_item, q_idx, chap_idx=None):
        chap_log_prefix = f"Chapter {chap_idx}, " if chap_idx is not None else ""
        required_keys = ["question", "options", "correct_answer", "explanation"]
        if not all(k in q_item for k in required_keys):
            raise ValueError(f"{chap_log_prefix}Question at index {q_idx} is missing required keys ({', '.join(required_keys)}).")
        if not isinstance(q_item["options"], list) or len(q_item["options"]) != 4:
            if isinstance(q_item["options"], list) and len(q_item["options"]) > 4:
                logger.warning(f"{chap_log_prefix}Question at index {q_idx} has more than 4 options. Truncating to 4.")
                q_item["options"] = q_item["options"][:4]
            elif isinstance(q_item["options"], list) and len(q_item["options"]) < 4:
                logger.warning(f"{chap_log_prefix}Question at index {q_idx} has less than 4 options. Padding with 'N/A'.")
                while len(q_item["options"]) < 4:
                    q_item["options"].append("N/A")
            else:
                raise ValueError(f"{chap_log_prefix}Question at index {q_idx} does not have 4 options after attempted adaptation.")

        correct_answer_val = q_item.get("correct_answer")
        try:
            correct_answer_val = int(correct_answer_val)
            if not (0 <= correct_answer_val < len(q_item["options"])):
                 raise ValueError("Index out of bounds")
            q_item["correct_answer"] = correct_answer_val
        except (ValueError, TypeError):
             logger.error(f"{chap_log_prefix}Correct answer index for question {q_idx} ('{q_item.get('question')[:30]}...') is not a valid integer index (0-3) or out of bounds. Got: {q_item.get('correct_answer')}. Setting to 0 as fallback.")
             q_item["correct_answer"] = 0


    def analyze_medical_document(self, document_content_excerpt):
        prompt = f"""Analyze this medical document thoroughly and provide a detailed professional report:

Document Content:
{document_content_excerpt}

Required Analysis:
1. Document type identification (lab report, discharge summary, etc.)
2. Key patient demographics (age, sex if available)
3. Critical medical findings (abnormal values, diagnoses)
4. Clinical significance of findings
5. Recommended follow-up actions
6. Potential differential diagnoses if relevant

Format your response with clear headings for each section."""
        
        messages = [{"role": "user", "content": prompt}]
        analysis, error = self._make_chat_completion_request(messages, model="gpt-4-turbo", max_tokens=4000, temperature=0.2)
        if error:
            return f"Document analysis failed: {error}", None
        return analysis, None

    def summarize_analysis(self, analysis_text):
        prompt = f"Summarize this medical analysis in 2-3 sentences for a quick overview:\n\n{analysis_text}"
        messages = [{"role": "user", "content": prompt}]
        summary, error = self._make_chat_completion_request(messages, model="gpt-4-turbo", max_tokens=200)
        if error:
            return f"Summary generation failed: {error}"
        return summary or "Could not generate summary."

    def get_chat_response(self, user_message, s3_documents_context=None, model="gpt-4-turbo"):
        system_prompt_content = """You are Dr. Max, a professional medical AI assistant specialized in medical education and exam preparation. 

As a medical education expert, you should:

🏥 **Clinical Excellence**: Provide accurate, evidence-based medical information
📚 **Educational Focus**: Structure responses for optimal learning and exam preparation  
🎯 **Comprehensive Coverage**: Address pathophysiology, diagnosis, treatment, and clinical significance
📝 **Exam-Oriented**: Include key points that commonly appear in medical examinations
🔬 **Research-Based**: Reference current medical guidelines and best practices

For each response:
1. **Structured Format**: Use clear headings and bullet points
2. **Key Terms**: Highlight important medical terminology in **bold**
3. **Clinical Reasoning**: Explain the "why" behind medical concepts
4. **Exam Tips**: Include memory aids, mnemonics, or exam-relevant points
5. **Differential Diagnosis**: When applicable, discuss related conditions
6. **Treatment Protocols**: Provide current evidence-based treatment approaches
7. **Learning Extensions**: Suggest related topics for further study

Always provide educational value and encourage critical thinking. If uncertain about recent updates, clearly state limitations and recommend consulting current medical literature."""

        messages = []

        if s3_documents_context:
            MAX_S3_CONTEXT_CHARS = 50000
            if len(s3_documents_context) > MAX_S3_CONTEXT_CHARS:
                s3_documents_context = s3_documents_context[:MAX_S3_CONTEXT_CHARS] + "... [Content truncated]"

            messages.append({
                "role": "system",
                "content": (
                    "You are Dr. Max, a medical AI. First check if the user's question can be answered from the "
                    "provided documents. Check full documents and proceed to answer as related to the question. "
                    "If yes, answer specifically from them. If not, state 'This specific information wasn't found "
                    "in our documents' and then proceed to answer from your general knowledge."
                )
            })
            messages.append({
                "role": "user",
                "content": f"MEDICAL DOCUMENTS:\n{s3_documents_context}\n\nQUESTION: {user_message}\n\nFirst check if this can be answered from the documents."
            })
        else:
            messages.append({"role": "system", "content": system_prompt_content})
            messages.append({"role": "user", "content": user_message})
        
        response_content, error = self._make_chat_completion_request(messages, model=model, max_tokens=2000)

        if error:
            return f"🔧 **Technical Issue**: I apologize, but I'm experiencing technical difficulties right now. Please try again in a moment, or rephrase your question. If the issue persists, please contact technical support.\n\nError details: {error}"
        
        if s3_documents_context:
            if "wasn't found in our documents" in response_content.lower() or \
               "not found in the documents" in response_content.lower() or \
               "not mentioned in the documents" in response_content.lower():
                logger.info("S3 context provided but AI indicated info not found. Falling back to general knowledge.")
                messages = [
                    {"role": "system", "content": system_prompt_content},
                    {"role": "user", "content": user_message}
                ]
                general_response_content, general_error = self._make_chat_completion_request(messages, model=model, max_tokens=2000)
                if general_error:
                     return f"🔧 **Technical Issue**: I apologize, but I'm experiencing technical difficulties right now. Please try again in a moment.\n\nError details: {general_error}"
                return "🧠 **Medical Knowledge Base**:\n\n" + (general_response_content or "No information available at this time.")
            else:
                return "� **From Medical Literature**:\n\n" + (response_content or "No relevant information found in available documents.")
        else:
            return "🩺 **Dr. Max's Medical Insights**:\n\n" + (response_content or "I'm unable to provide information on that topic at this time.")

openai_service = OpenAIService()