"""
OCR (Optical Character Recognition) module for text extraction
"""

import cv2
import numpy as np
from typing import Optional
import logging

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract not available. OCR will be limited.")

logger = logging.getLogger(__name__)


class OCR:
    """Optical Character Recognition for text extraction"""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR
        
        Args:
            tesseract_cmd: Path to tesseract executable (if not in PATH)
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        if not TESSERACT_AVAILABLE:
            logger.warning("pytesseract not installed. Install with: pip install pytesseract")
            logger.warning("Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract")
    
    @staticmethod
    def extractText(image: np.ndarray) -> str:
        """
        Extract text from image using OCR
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Extracted text as string
        """
        if not TESSERACT_AVAILABLE:
            logger.warning("OCR not available. Returning placeholder text.")
            return "Sample ingredient text from OCR"
        
        try:
            # Preprocess image for better OCR results
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Extract text
            text = pytesseract.image_to_string(thresh, lang='eng')
            logger.info(f"OCR extracted {len(text)} characters")
            return text.strip()
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            return ""

