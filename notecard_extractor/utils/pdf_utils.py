#!/usr/bin/env python3
"""
PDF utility functions.
Handles PDF reading and image extraction from PDF pages.
"""

import io
from typing import Optional
from pypdf import PdfReader
from PIL import Image


def extract_images_from_pdf_page(page, page_num: int) -> Optional[Image.Image]:
    """
    Extract the first image from a PDF page.
    
    Args:
        page: PyPDF page object
        page_num: Page number (0-indexed) for error reporting
        
    Returns:
        PIL Image if found, None otherwise
    """
    for image_file_object in page.images:
        try:
            # Get image data
            image_data = image_file_object.data
            
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))
            return image
            
        except Exception:
            # Continue to next image if this one fails
            continue
    
    return None


def read_pdf_from_bytes(pdf_data: bytes) -> PdfReader:
    """
    Read PDF from bytes and return PdfReader object.
    
    Args:
        pdf_data: PDF file data as bytes
        
    Returns:
        PdfReader object
    """
    pdf_stream = io.BytesIO(pdf_data)
    return PdfReader(pdf_stream)
