"""
Camera handling module for capturing images
"""

import cv2
import numpy as np
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class Camera:
    """Camera interface for capturing images"""
    
    def __init__(self, camera_index: int = 0):
        """
        Initialize camera
        
        Args:
            camera_index: Index of camera device (default: 0)
        """
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
    
    def activate(self):
        """Activate camera"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                raise RuntimeError(f"Could not open camera {self.camera_index}")
            
            # Test camera by reading a frame
            ret, test_frame = self.cap.read()
            if not ret:
                raise RuntimeError("Camera opened but failed to capture test frame")
            
            logger.info(f"Camera {self.camera_index} activated successfully")
        except Exception as e:
            logger.error(f"Failed to activate camera: {e}")
            self.cap = None
            raise
    
    def capture(self) -> np.ndarray:
        """
        Capture image from camera
        
        Returns:
            Image as numpy array
        """
        if self.cap is None:
            raise RuntimeError("Camera not activated. Call activate() first.")
        
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to capture image from camera")
        
        logger.info("Live image captured from camera")
        return frame
    
    def release(self):
        """Release camera resources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info("Camera released")
    
    def __enter__(self):
        """Context manager entry"""
        self.activate()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()

