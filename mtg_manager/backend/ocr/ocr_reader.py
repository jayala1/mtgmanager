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
import os

try:
    import pytesseract
    
    # Set Tesseract path for Windows (adjust path as needed)
    import platform
    if platform.system() == "Windows":
        # Common Tesseract installation paths
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', 'user'))
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
    
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
    
    def __init__(self, preferred_engine: str = "easyocr"):
        """Initialize OCR reader with preferred engine."""
        self.logger = logging.getLogger(__name__)
        self.preferred_engine = preferred_engine
        self.easyocr_reader = None
        self.tesseract_available = TESSERACT_AVAILABLE
        self.easyocr_available = EASYOCR_AVAILABLE
        
        # Initialize EasyOCR if available
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en'])
                self.logger.info("EasyOCR initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize EasyOCR: {e}")
                self.easyocr_available = False
        
        # Log available engines
        available_engines = []
        if self.tesseract_available:
            available_engines.append("Tesseract")
        if self.easyocr_available:
            available_engines.append("EasyOCR")
        
        self.logger.info(f"Available OCR engines: {', '.join(available_engines) if available_engines else 'None'}")
        
        # Set fallback preference if preferred engine is not available
        if preferred_engine == "tesseract" and not self.tesseract_available:
            self.logger.warning("Tesseract not available, will use EasyOCR")
            self.preferred_engine = "easyocr"
        elif preferred_engine == "easyocr" and not self.easyocr_available:
            self.logger.warning("EasyOCR not available, will use Tesseract")
            self.preferred_engine = "tesseract"
    
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
        if not self.tesseract_available:
            self.logger.debug("Tesseract not available")
            return []
        
        try:
            # Configure Tesseract for better card name detection
            config = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\' ,-'
            
            text = pytesseract.image_to_string(image, config=config)
            
            # Clean and split text into lines
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            self.logger.debug(f"Tesseract extracted {len(lines)} lines: {lines}")
            return lines
            
        except Exception as e:
            self.logger.error(f"Tesseract OCR failed: {e}")
            return []
    
    def extract_text_easyocr(self, image: np.ndarray) -> List[str]:
        """Extract text using EasyOCR."""
        if not self.easyocr_available or not self.easyocr_reader:
            self.logger.debug("EasyOCR not available")
            return []
        
        try:
            results = self.easyocr_reader.readtext(image)
            
            # Extract text from results with confidence filtering
            lines = []
            for result in results:
                text = result[1]
                confidence = result[2]
                if confidence > 0.3:  # Lower confidence threshold for better detection
                    lines.append(text)
            
            self.logger.debug(f"EasyOCR extracted {len(lines)} lines: {lines}")
            return lines
            
        except Exception as e:
            self.logger.error(f"EasyOCR failed: {e}")
            return []
    
    def identify_card_name_from_lines(self, lines: List[str]) -> Optional[str]:
        """Try to identify the card name from detected text lines."""
        if not lines:
            return None
        
        # Sort lines by length (longer lines more likely to be card names)
        sorted_lines = sorted(lines, key=len, reverse=True)
        
        for line in sorted_lines:
            # Clean the line
            cleaned = line.strip(' .,\'"()[]{}')
            
            # Skip very short or very long strings
            if len(cleaned) < 3 or len(cleaned) > 50:
                continue
                
            # Skip lines that are mostly numbers or symbols
            if not any(c.isalpha() for c in cleaned):
                continue
                
            # Skip common non-name text patterns
            skip_patterns = [
                'legendary', 'creature', 'instant', 'sorcery', 'artifact', 
                'enchantment', 'planeswalker', 'land', 'flying', 'trample',
                'first strike', 'deathtouch', 'lifelink', 'vigilance',
                'whenever', 'target', 'mana cost', 'converted', 'enters',
                'battlefield', 'graveyard', 'exile', 'draw', 'damage',
                'destroy', 'counter', 'spell', 'ability', 'activated',
                'triggered', 'static', 'upkeep', 'end step', 'combat',
                'main phase', 'beginning', 'untap', 'tap', 'untapped'
            ]
            
            if any(pattern in cleaned.lower() for pattern in skip_patterns):
                continue
                
            # Skip if it's mostly punctuation
            alpha_count = sum(1 for c in cleaned if c.isalpha())
            if alpha_count < len(cleaned) * 0.5:
                continue
                
            # This looks like a potential card name
            self.logger.debug(f"Potential card name identified: '{cleaned}'")
            return cleaned
        
        # If no good candidate found, return the first non-empty line
        for line in lines:
            cleaned = line.strip()
            if len(cleaned) >= 3:
                self.logger.debug(f"Fallback card name: '{cleaned}'")
                return cleaned
        
        return None
    
    def extract_card_name(self, image: np.ndarray) -> Optional[str]:
        """Extract card name from image using OCR with fallback."""
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Try primary engine first
            primary_lines = []
            if self.preferred_engine == "tesseract" and self.tesseract_available:
                self.logger.debug("Trying Tesseract (primary)")
                primary_lines = self.extract_text_tesseract(processed_image)
            elif self.preferred_engine == "easyocr" and self.easyocr_available:
                self.logger.debug("Trying EasyOCR (primary)")
                primary_lines = self.extract_text_easyocr(processed_image)
            
            # Try to get card name from primary engine
            if primary_lines:
                card_name = self.identify_card_name_from_lines(primary_lines)
                if card_name:
                    self.logger.info(f"Primary engine ({self.preferred_engine}) detected: '{card_name}'")
                    return card_name
            
            # Fallback to secondary engine
            secondary_lines = []
            if self.preferred_engine == "tesseract" and self.easyocr_available:
                self.logger.debug("Trying EasyOCR (fallback)")
                secondary_lines = self.extract_text_easyocr(processed_image)
            elif self.preferred_engine == "easyocr" and self.tesseract_available:
                self.logger.debug("Trying Tesseract (fallback)")
                secondary_lines = self.extract_text_tesseract(processed_image)
            
            # Try to get card name from secondary engine
            if secondary_lines:
                card_name = self.identify_card_name_from_lines(secondary_lines)
                if card_name:
                    fallback_engine = "easyocr" if self.preferred_engine == "tesseract" else "tesseract"
                    self.logger.info(f"Fallback engine ({fallback_engine}) detected: '{card_name}'")
                    return card_name
            
            # If both engines tried, combine results and try again
            all_lines = primary_lines + secondary_lines
            if all_lines:
                card_name = self.identify_card_name_from_lines(all_lines)
                if card_name:
                    self.logger.info(f"Combined results detected: '{card_name}'")
                    return card_name
            
            self.logger.warning("No card name detected by any OCR engine")
            return None
            
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
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