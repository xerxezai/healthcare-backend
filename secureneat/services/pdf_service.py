import fitz # PyMuPDF
import logging

logger = logging.getLogger(__name__)

class PDFService:
    def extract_text_from_pdf_buffer(self, pdf_buffer, max_chars=None):
        try:
            doc = fitz.open(stream=pdf_buffer, filetype="pdf")
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text("text") + "\n"
            
            if max_chars and len(text) > max_chars:
                text = text[:max_chars]
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF buffer: {e}")
            # Consider re-raising or returning a specific error message
            raise ValueError(f"Could not process PDF: {e}")


    def extract_text_from_pdf_filepath(self, file_path, max_chars=None):
        try:
            doc = fitz.open(file_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text("text") + "\n"

            if max_chars and len(text) > max_chars:
                text = text[:max_chars]
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF file {file_path}: {e}")
            raise ValueError(f"Could not process PDF file: {e}")

pdf_service = PDFService()