"""
Barcode detection and reading module
"""

import cv2
import numpy as np
from typing import Optional
import logging

try:
    from pyzbar.pyzbar import decode
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    decode = None
    logging.warning("pyzbar not available. Barcode detection will be limited.")

logger = logging.getLogger(__name__)


class BarcodeDetector:
    """Barcode detection and reading"""
    
    def __init__(self):
        """Initialize barcode detector"""
        if not PYZBAR_AVAILABLE:
            logger.warning("pyzbar not installed. Install with: pip install pyzbar")
    
    def detected(self, image: np.ndarray) -> bool:
        """
        Check if barcode is detected in image
        
        Args:
            image: Input image as numpy array
            
        Returns:
            True if barcode detected, False otherwise
        """
        if not PYZBAR_AVAILABLE:
            # Fallback: simple edge detection check
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            edges = cv2.Canny(gray, 50, 150)
            # Simple heuristic: if many edges detected, might have barcode
            return np.sum(edges > 0) > 1000
        
        try:
            barcodes = decode(image)
            detected = len(barcodes) > 0
            logger.info(f"Barcode detection: {detected}")
            return detected
        except Exception as e:
            logger.error(f"Error in barcode detection: {e}")
            return False
    
    def read(self, image: np.ndarray) -> str:
        """
        Read barcode data from image
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Barcode data as string
        """
        if not PYZBAR_AVAILABLE:
            raise RuntimeError("pyzbar not available. Cannot read barcode.")
        
        try:
            barcodes = decode(image)
            if not barcodes:
                raise ValueError("No barcode found in image")
            
            barcode_data = barcodes[0].data.decode('utf-8')
            logger.info(f"Barcode read: {barcode_data}")
            return barcode_data
        except Exception as e:
            logger.error(f"Error reading barcode: {e}")
            raise

