# backend/ai/ollama_client.py
"""
Ollama client for MTG card recognition using vision models.
"""

import requests
import json
import base64
import logging
from typing import Optional, Dict, Any, List
import cv2
import numpy as np
from PIL import Image
import io

class OllamaClient:
    """Client for interacting with Ollama vision models."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize Ollama client."""
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.available_models = []
        self.selected_model = None
        
        # Check if Ollama is running
        self.is_available = self.check_availability()
        if self.is_available:
            self.refresh_models()
    
    def check_availability(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info("Ollama is available")
                return True
            else:
                self.logger.warning(f"Ollama responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Ollama not available: {e}")
            return False
    
    def refresh_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                self.available_models = []
                
                for model in data.get('models', []):
                    model_name = model.get('name', '')
                    # Filter for vision-capable models
                    if any(vision_indicator in model_name.lower() for vision_indicator in 
                           ['llava', 'vision', 'multimodal', 'bakllava', 'moondream']):
                        self.available_models.append(model_name)
                
                self.logger.info(f"Found {len(self.available_models)} vision models")
                return self.available_models
            else:
                self.logger.error("Failed to get models from Ollama")
                return []
        except Exception as e:
            self.logger.error(f"Error getting models: {e}")
            return []
    
    def set_model(self, model_name: str) -> bool:
        """Set the model to use for vision tasks."""
        if model_name in self.available_models:
            self.selected_model = model_name
            self.logger.info(f"Selected model: {model_name}")
            return True
        else:
            self.logger.error(f"Model {model_name} not available")
            return False
    
    def image_to_base64(self, image: np.ndarray) -> str:
        """Convert OpenCV image to base64 string."""
        # Convert BGR to RGB
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=85)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return image_base64
    
    def analyze_card_image(self, image: np.ndarray, prompt: str = None) -> Optional[Dict[str, Any]]:
        """Analyze a Magic card image using the selected vision model."""
        if not self.is_available:
            self.logger.error("Ollama not available")
            return None
        
        if not self.selected_model:
            self.logger.error("No model selected")
            return None
        
        try:
            # Convert image to base64
            image_b64 = self.image_to_base64(image)
            
            # Default prompt for MTG card analysis
            if not prompt:
                prompt = """Analyze this Magic: The Gathering card image and extract the following information in JSON format:

{
    "name": "exact card name",
    "mana_cost": "mana cost (e.g., {3}{R}{G})",
    "type_line": "card type line",
    "power": "creature power (if applicable)",
    "toughness": "creature toughness (if applicable)",
    "oracle_text": "card text/abilities",
    "set_symbol_visible": true/false,
    "condition": "estimated condition based on visible wear",
    "confidence": "how confident you are (1-10)"
}

Focus on the card name accuracy. If you can't read something clearly, indicate uncertainty. Only return the JSON, no other text."""
            
            # Prepare request
            data = {
                "model": self.selected_model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False
            }
            
            self.logger.info(f"Sending card image to {self.selected_model}")
            
            # Send request to Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=60  # Vision models can be slow
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                # Try to parse JSON from response
                card_data = self.parse_card_response(response_text)
                if card_data:
                    self.logger.info(f"Successfully analyzed card: {card_data.get('name', 'Unknown')}")
                    return card_data
                else:
                    self.logger.warning("Could not parse card data from response")
                    return {"raw_response": response_text}
            else:
                self.logger.error(f"Ollama request failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error analyzing card image: {e}")
            return None
    
    def parse_card_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the model's response and extract card data."""
        try:
            # Try to extract JSON from response
            import re
            
            # Look for JSON-like content
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                card_data = json.loads(json_str)
                
                # Validate required fields
                if 'name' in card_data and card_data['name']:
                    return card_data
            
            # If no valid JSON, try to extract name manually
            lines = response_text.split('\n')
            for line in lines:
                if 'name' in line.lower() and ':' in line:
                    name = line.split(':', 1)[1].strip().strip('"')
                    if name:
                        return {"name": name, "raw_response": response_text}
            
            return None
            
        except json.JSONDecodeError:
            self.logger.warning("Could not parse JSON from model response")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            return None
    
    def get_simple_card_name(self, image: np.ndarray) -> Optional[str]:
        """Get just the card name using a simple prompt."""
        simple_prompt = """Look at this Magic: The Gathering card and tell me the exact card name. 
Only respond with the card name, nothing else. If you can't read it clearly, say 'UNCLEAR'."""
        
        result = self.analyze_card_image(image, simple_prompt)
        if result:
            if 'name' in result:
                return result['name']
            elif 'raw_response' in result:
                # Clean up the raw response
                name = result['raw_response'].strip()
                if name and name != 'UNCLEAR':
                    return name
        
        return None