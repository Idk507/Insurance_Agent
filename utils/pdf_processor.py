"""
PDF Processing Utilities

This module provides utilities for handling PDF files in the insurance form processing system:
- PDF file validation and verification
- File size and format checks
- PDF content extraction helpers
- Error handling for corrupted files

Technology: PyMuPDF for PDF processing
"""

import fitz  # PyMuPDF
import os
from typing import Optional, Tuple
from pathlib import Path


class PDFProcessor:
    """Utility class for PDF processing operations"""

    def __init__(self, max_file_size_mb: int = 10):
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    def validate_pdf_file(self, file_content: bytes) -> Tuple[bool, str]:
        
        """
        Validate PDF file content

        Args:
            file_content: PDF file content as bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        
        try:
            if len(file_content) > self.max_file_size_bytes:
                return False, f"File size exceeds {self.max_file_size_mb}MB limit"

            if len(file_content) == 0:
                return False, "File is empty"

            doc = fitz.open(stream=file_content, filetype="pdf")
            if len(doc) == 0:
                doc.close()
                return False, "PDF file has no pages"

            doc.close()
            return True, "Valid PDF file"

        except Exception as e:
            return False, f"Invalid PDF file: {str(e)}"

    def get_pdf_info(self, file_content: bytes) -> dict:
        
        """
        Get basic information about the PDF file

        Args:
            file_content: PDF file content as bytes

        Returns:
            Dictionary with PDF information
        """
        
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            info = {
                "page_count": len(doc),
                "file_size_bytes": len(file_content),
                "file_size_mb": round(len(file_content) / (1024 * 1024), 2),
                "metadata": doc.metadata,
                "is_encrypted": doc.is_encrypted,
                "is_pdf": doc.is_pdf
            }
            doc.close()
            return info

        except Exception as e:
            return {"error": f"Failed to get PDF info: {str(e)}"}

    def extract_text_preview(self, file_content: bytes, max_chars: int = 500) -> str:
        
        """
        Extract a preview of text from the first page

        Args:
            file_content: PDF file content as bytes
            max_chars: Maximum characters to extract

        Returns:
            Preview text string
        """
        
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            if len(doc) == 0:
                return "No pages found in PDF"

            first_page = doc.load_page(0)
            text = first_page.get_text()
            doc.close()

            return text[:max_chars] + "..." if len(text) > max_chars else text

        except Exception as e:
            return f"Failed to extract preview: {str(e)}"

    def save_uploaded_file(self, file_content: bytes, filename: str, upload_dir: str = "data/uploaded") -> str:
        
        """
        Save uploaded PDF file to disk

        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            upload_dir: Directory to save file

        Returns:
            Path to saved file
        """
        
        try:
            Path(upload_dir).mkdir(parents=True, exist_ok=True)
            safe_filename = self._generate_safe_filename(filename)
            file_path = os.path.join(upload_dir, safe_filename)

            with open(file_path, "wb") as f:
                f.write(file_content)

            return file_path

        except Exception as e:
            raise Exception(f"Failed to save file: {str(e)}")

    def _generate_safe_filename(self, filename: str) -> str:
        
        """Generate a safe filename for saving"""
        
        import re
        from datetime import datetime

        safe_name = re.sub(r'[^\w\-_\.]', '_', filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(safe_name)
        return f"{name}_{timestamp}{ext}"


# Create global instance
pdf_processor = PDFProcessor()
