"""OCR Agent - Extracts text from PDF insurance forms - Fixed for serialization"""

import fitz  # PyMuPDF
import io
import tempfile
import os
from typing import Optional, Dict, Any
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.reasoning import ReasoningTools
from agno.utils.log import logger
from config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_GPT_DEPLOYMENT
)
from config.client_manager import get_llm_client
from utils.exception_handling import setup_openai_exception_suppression  # Handles OpenAI cleanup issues

# Optional imports for alternative OCR methods
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available - using PyMuPDF only")

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract/pdf2image not available - OCR fallback disabled")

class OCRTool:
    name = "ocr_extraction"
    description = "Extracts text and tables from PDF using multiple OCR methods with fallback support."

    def __init__(self):
        self.methods = []
        if True:  # PyMuPDF is always available since it's in requirements
            self.methods.append("pymupdf")
        if PDFPLUMBER_AVAILABLE:
            self.methods.append("pdfplumber")
        if TESSERACT_AVAILABLE:
            self.methods.append("tesseract")
        
        logger.info(f"OCR methods available: {self.methods}")

    def _extract_with_pymupdf(self, pdf_content: bytes) -> str:
        """Extract text using PyMuPDF - properly handles serialization"""
        try:
            # Create a temporary file to avoid stream issues
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file.flush()
                temp_path = temp_file.name
            
            extracted_text = ""
            try:
                # Open document from file path
                doc = fitz.open(temp_path)
                
                # Extract text page by page - immediately convert to string
                pages_text = []
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    page_text = page.get_text()
                    pages_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                    # Release page reference immediately
                    del page
                
                # Close document immediately and release resources
                doc.close()
                del doc
                
                # Combine all pages into a single string
                extracted_text = "\n".join(pages_text)
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"PyMuPDF extraction error: {e}")
            raise
            
        return extracted_text

    def _extract_with_pdfplumber(self, pdf_content: bytes) -> str:
        """Extract text using pdfplumber as alternative method"""
        try:
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                pages_text = []
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    pages_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                
                return "\n".join(pages_text)
                
        except Exception as e:
            logger.error(f"PDFPlumber extraction error: {e}")
            raise

    def _extract_with_tesseract(self, pdf_content: bytes) -> str:
        """Extract text using Tesseract OCR as fallback for image-based PDFs"""
        try:
            # Convert PDF to images
            images = convert_from_bytes(pdf_content, dpi=200)
            
            pages_text = []
            for page_num, image in enumerate(images):
                # Perform OCR on the image
                page_text = pytesseract.image_to_string(image, lang='eng+msa')  # English + Malay
                pages_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                # Release image reference
                del image
            
            return "\n".join(pages_text)
            
        except Exception as e:
            logger.error(f"Tesseract extraction error: {e}")
            raise

    def run(self, pdf_content: bytes) -> str:
        """Main extraction method - returns only serializable string data"""
        logger.info(f"Running OCR on PDF with {len(self.methods)} available methods")
        
        if not isinstance(pdf_content, bytes):
            return "OCR Error: Invalid input - expected bytes"
        
        last_error = None
        
        for method in self.methods:
            try:
                logger.info(f"Attempting OCR with method: {method}")
                
                if method == "pymupdf":
                    result = self._extract_with_pymupdf(pdf_content)
                elif method == "pdfplumber" and PDFPLUMBER_AVAILABLE:
                    result = self._extract_with_pdfplumber(pdf_content)
                elif method == "tesseract" and TESSERACT_AVAILABLE:
                    result = self._extract_with_tesseract(pdf_content)
                else:
                    continue
                
                # Validate result - ensure it's a string
                if isinstance(result, str) and len(result.strip()) > 10:
                    logger.info(f"OCR successful with method: {method}")
                    logger.info(f"Extracted {len(result)} characters, {len(result.split())} words")
                    return result
                else:
                    logger.warning(f"Method {method} returned insufficient content")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Method {method} failed: {e}")
                continue
        
        # If all methods failed
        error_msg = f"All OCR methods failed. Last error: {last_error}"
        logger.error(error_msg)
        return f"OCR Error: {error_msg}"

# Serializable OCR function for use with agents
def extract_text_from_pdf(pdf_content: bytes) -> Dict[str, Any]:
    """
    Serializable function that extracts text from PDF.
    Returns a dictionary with extracted text and metadata.
    """
    try:
        ocr_tool = OCRTool()
        extracted_text = ocr_tool.run(pdf_content)
        
        return {
            "success": True,
            "extracted_text": extracted_text,
            "text_length": len(extracted_text),
            "word_count": len(extracted_text.split()) if extracted_text else 0,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "extracted_text": "",
            "text_length": 0,
            "word_count": 0,
            "error": str(e)
        }

ocr_agent = Agent(
    name="OCR Agent",
    model=get_llm_client(),
    tools=[ReasoningTools(add_instructions=True), OCRTool()],
    instructions=[
        "You are an OCR specialist for insurance documents.",
        "Use the ocr_extraction tool to extract text from uploaded PDFs.",
        "The tool uses multiple OCR methods with automatic fallback for maximum reliability.",
        "Always validate that meaningful text was extracted before proceeding.",
        "If OCR fails completely, clearly indicate the failure and suggest manual review.",
        "Return clean, well-structured text output with clear page separations.",
        "Focus on preserving important formatting like tables and field structures.",
        "Only return string data to avoid serialization issues."
    ],
    description="Extracts text and tables from insurance PDFs using multiple OCR methods with fallback support",
    markdown=True,
)
