import pandas as pd
import docx2txt
from docx import Document as DocxDocument # python-docx
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

# Assuming pdf_service is accessible, e.g., from secureneat or a shared location
# If not, you might need to replicate its functionality or adjust the import
try:
    from secureneat.services.pdf_service import pdf_service
except ImportError:
    logger.warning("secureneat.services.pdf_service not found. PDF parsing will be limited.")
    pdf_service = None


def parse_file_content(file_obj, file_name):
    content = ""
    file_extension = file_name.split('.')[-1].lower()
    
    # Ensure file_obj is a BytesIO stream if it's an UploadedFile
    if hasattr(file_obj, 'read'):
        # For Django UploadedFile, it's already a file-like object
        # For BytesIO, ensure it's at the beginning
        if hasattr(file_obj, 'seek') and callable(file_obj.seek):
             file_obj.seek(0)
    else:
        # If it's raw bytes, wrap it in BytesIO
        file_obj = BytesIO(file_obj)


    if file_extension == 'txt':
        content = file_obj.read().decode('utf-8', errors='ignore')
    elif file_extension == 'docx':
        try:
            content = docx2txt.process(file_obj)
        except Exception as e_docx2txt:
            logger.warning(f"docx2txt failed for {file_name}: {e_docx2txt}. Trying python-docx.")
            try:
                file_obj.seek(0) # Reset stream position
                doc = DocxDocument(file_obj)
                content = "\n".join([para.text for para in doc.paragraphs])
            except Exception as e_python_docx:
                 raise ValueError(f"Failed to parse DOCX {file_name} with both methods: {e_docx2txt}, {e_python_docx}")
    elif file_extension in ['xlsx', 'xls']:
        try:
            xls = pd.ExcelFile(file_obj)
            all_text = []
            for sheet_name in xls.sheet_names:
                df = xls.parse(sheet_name, header=None)
                sheet_text = df.astype(str).apply(lambda x: ' '.join(x.dropna()), axis=1).str.cat(sep='\n')
                all_text.append(sheet_text)
            content = "\n\n--- New Sheet: {} ---\n\n".format(sheet_name).join(all_text) # Corrected join
        except Exception as e:
            raise ValueError(f"Failed to parse Excel file {file_name}: {e}")
    elif file_extension == 'pdf':
        if pdf_service:
            file_obj.seek(0)
            pdf_buffer_content = file_obj.read()
            content = pdf_service.extract_text_from_pdf_buffer(pdf_buffer_content)
        else:
            raise ValueError("PDF parsing service is not available.")
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")
    return content.strip()