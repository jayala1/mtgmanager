# backend/ocr/ocr_reader.py
"""
OCR functionality for card scanning in MTG Collection Manager.
"""

import logging
import cv2
import numpy as np
from typing import Optional, List
import threading
import time

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

class OCRReader:
    """Handles OCR operations for card scanning."""
    
    def __init__(self, preferred_engine: str = "tesseract"):
        """Initialize OCR reader with preferred engine."""
        self.logger = logging.getLogger(__name__)
        self.preferred_engine = preferred_engine
        self.easyocr_reader = None
        
        # Initialize EasyOCR if available and preferred
        if preferred_engine == "easyocr" and EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en'])
                self.logger.info("EasyOCR initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize EasyOCR: {e}")
        
        # Check Tesseract availability
        if preferred_engine == "tesseract" and not TESSERACT_AVAILABLE:
            self.logger.warning("Tesseract not available, falling back to EasyOCR")
            self.preferred_engine = "easyocr"
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up the image
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def extract_text_tesseract(self, image: np.ndarray) -> List[str]:
        """Extract text using Tesseract OCR."""
        if not TESSERACT_AVAILABLE:
            return []
        
        try:
            # Configure Tesseract for better card name detection
            config = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\' ,-'
            
            text = pytesseract.image_to_string(image, config=config)
            
            # Clean and split text into lines
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return lines
            
        except Exception as e:
            self.logger.error(f"Tesseract OCR failed: {e}")
            return []
    
    def extract_text_easyocr(self, image: np.ndarray) -> List[str]:
        """Extract text using EasyOCR."""
        if not self.easyocr_reader:
            return []
        
        try:
            results = self.easyocr_reader.readtext(image)
            
            # Extract text from results
            lines = [result[1] for result in results if result[2] > 0.5]  # Confidence > 0.5
            return lines
            
        except Exception as e:
            self.logger.error(f"EasyOCR failed: {e}")
            return []
    
    def extract_card_name(self, image: np.ndarray) -> Optional[str]:
        """Extract card name from image using OCR."""
        # Preprocess image
        processed_image = self.preprocess_image(image)
        
        # Extract text using preferred engine
        if self.preferred_engine == "tesseract":
            lines = self.extract_text_tesseract(processed_image)
        else:
            lines = self.extract_text_easyocr(processed_image)
        
        if not lines:
            return None
        
        # Try to identify the card name (usually the first substantial line)
        for line in lines:
            # Filter out very short strings and common non-name text
            if len(line) > 2 and not line.isdigit():
                # Clean up the line
                cleaned = line.strip(' .,\'"')
                if len(cleaned) > 2:
                    return cleaned
        
        return None

class CameraCapture:
    """Handles camera operations for card scanning."""
    
    def __init__(self, camera_index: int = 0):
        """Initialize camera capture."""
        self.camera_index = camera_index
        self.logger = logging.getLogger(__name__)
        self.cap = None
        self.is_active = False
    
    def start_camera(self) -> bool:
        """Start the camera."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                self.logger.error("Failed to open camera")
                return False
            
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            self.is_active = True
            self.logger.info("Camera started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start camera: {e}")
            return False
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame from the camera."""
        if not self.cap or not self.is_active:
            return None
        
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None
    
    def stop_camera(self):
        """Stop the camera and release resources."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_active = False
        self.logger.info("Camera stopped")