"""
Advanced Food Label and Barcode Identification Module
Uses Gemini AI Vision and advanced OCR for accurate product identification
"""

import logging
import base64
import requests
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image
import io

# Import configuration
try:
    from config import Config
except ImportError:
    class Config:
        GEMINI_API_KEY = None

logger = logging.getLogger(__name__)


class AdvancedFoodIdentifier:
    """Advanced food product identifier using AI Vision and OCR"""
    
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.vision_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"
        self.text_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
    def identify_product_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Identify product from image using AI Vision and OCR
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with product information
        """
        try:
            if not self.api_key:
                logger.warning("Gemini API key not configured")
                return self._get_fallback_identification(image_path)
            
            # Convert image to base64
            image_data = self._encode_image(image_path)
            
            # Use Gemini Vision for comprehensive analysis
            product_info = self._analyze_with_vision(image_data)
            
            if product_info:
                return product_info
            else:
                # Fallback to text-based analysis
                return self._analyze_with_text(image_data)
                
        except Exception as e:
            logger.error(f"Error in advanced product identification: {str(e)}")
            return self._get_fallback_identification(image_path)
    
    def _encode_image(self, image_path: str) -> str:
        """Convert image to base64"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                max_size = (1024, 1024)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to bytes
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                image_bytes = buffered.getvalue()
                
                return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image: {str(e)}")
            return None
    
    def _analyze_with_vision(self, image_data: str) -> Optional[Dict[str, Any]]:
        """Analyze image using Gemini Vision API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            prompt = """
            Analyze this food product image and extract the following information:
            
            1. Product Name: The specific name of the product
            2. Brand: The manufacturer/brand name
            3. Barcode: Any barcode numbers visible (EAN-13, UPC-A, etc.)
            4. Product Type: Category (e.g., "Soda", "Chips", "Cookies", "Juice")
            5. Key Ingredients: Main ingredients visible on the label
            6. Net Weight: Package size/weight if visible
            7. Flavor/Variety: Specific flavor or variety
            
            Format your response as JSON:
            {
                "product_name": "exact product name",
                "brand": "brand name",
                "barcode": "barcode number if visible",
                "product_type": "product category",
                "key_ingredients": ["ingredient1", "ingredient2"],
                "net_weight": "weight/size",
                "flavor_variety": "flavor or variety",
                "confidence": "high/medium/low"
            }
            
            Be precise and extract exactly what you can see from the label.
            """
            
            data = {
                'contents': [{
                    'parts': [
                        {
                            'text': prompt
                        },
                        {
                            'inline_data': {
                                'mime_type': 'image/jpeg',
                                'data': image_data
                            }
                        }
                    ]
                }],
                'generationConfig': {
                    'temperature': 0.1,
                    'topK': 32,
                    'topP': 0.95,
                    'maxOutputTokens': 1024,
                }
            }
            
            response = requests.post(
                self.vision_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    ai_response = result['candidates'][0]['content']['parts'][0]['text']
                    return self._parse_vision_response(ai_response)
            
            logger.error(f"Vision API error: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error in vision analysis: {str(e)}")
            return None
    
    def _analyze_with_text(self, image_data: str) -> Optional[Dict[str, Any]]:
        """Analyze image using text-based OCR approach"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            prompt = """
            Extract all text from this food product image and identify:
            
            1. Product name (usually the largest text)
            2. Brand name (often in logo or top of package)
            3. Any barcode numbers
            4. Ingredients list
            5. Net weight/size
            6. Any nutritional information
            
            Format as JSON:
            {
                "extracted_text": "all visible text",
                "product_name": "identified product name",
                "brand": "identified brand",
                "barcode": "barcode if found",
                "ingredients": ["ingredient1", "ingredient2"],
                "net_weight": "weight/size",
                "confidence": "high/medium/low"
            }
            """
            
            data = {
                'contents': [{
                    'parts': [
                        {
                            'text': prompt
                        },
                        {
                            'inline_data': {
                                'mime_type': 'image/jpeg',
                                'data': image_data
                            }
                        }
                    ]
                }],
                'generationConfig': {
                    'temperature': 0.2,
                    'topK': 40,
                    'topP': 0.95,
                    'maxOutputTokens': 2048,
                }
            }
            
            response = requests.post(
                self.text_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    ai_response = result['candidates'][0]['content']['parts'][0]['text']
                    return self._parse_text_response(ai_response)
            
            return None
            
        except Exception as e:
            logger.error(f"Error in text analysis: {str(e)}")
            return None
    
    def _parse_vision_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse vision API response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                # Standardize the response
                return {
                    'success': True,
                    'product_name': data.get('product_name', ''),
                    'brand': data.get('brand', ''),
                    'barcode': data.get('barcode', ''),
                    'product_type': data.get('product_type', ''),
                    'ingredients': data.get('key_ingredients', []),
                    'net_weight': data.get('net_weight', ''),
                    'flavor': data.get('flavor_variety', ''),
                    'confidence': data.get('confidence', 'medium'),
                    'method': 'vision'
                }
        except Exception as e:
            logger.error(f"Error parsing vision response: {str(e)}")
            return None
    
    def _parse_text_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse text-based response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                # Standardize the response
                return {
                    'success': True,
                    'product_name': data.get('product_name', ''),
                    'brand': data.get('brand', ''),
                    'barcode': data.get('barcode', ''),
                    'product_type': '',
                    'ingredients': data.get('ingredients', []),
                    'net_weight': data.get('net_weight', ''),
                    'flavor': '',
                    'confidence': data.get('confidence', 'medium'),
                    'method': 'text'
                }
        except Exception as e:
            logger.error(f"Error parsing text response: {str(e)}")
            return None
    
    def _get_fallback_identification(self, image_path: str) -> Dict[str, Any]:
        """Fallback identification when AI is not available"""
        return {
            'success': False,
            'product_name': 'Unknown Product',
            'brand': 'Unknown Brand',
            'barcode': '',
            'product_type': 'Food Product',
            'ingredients': ['Water', 'Sugar', 'Natural Flavors'],
            'net_weight': '',
            'flavor': '',
            'confidence': 'low',
            'method': 'fallback',
            'error': 'AI identification not available'
        }
    
    def extract_barcode_from_image(self, image_path: str) -> Optional[str]:
        """Extract barcode using AI vision"""
        try:
            if not self.api_key:
                return None
            
            image_data = self._encode_image(image_path)
            if not image_data:
                return None
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            prompt = """
            Look carefully at this image and find any barcodes. 
            If you find a barcode, read the numbers exactly as they appear.
            
            Common barcode formats:
            - EAN-13: 13 digits (most common worldwide)
            - UPC-A: 12 digits (common in US)
            - Code 128: Variable length
            
            Respond with ONLY the barcode number if found, or "No barcode found" if none visible.
            """
            
            data = {
                'contents': [{
                    'parts': [
                        {
                            'text': prompt
                        },
                        {
                            'inline_data': {
                                'mime_type': 'image/jpeg',
                                'data': image_data
                            }
                        }
                    ]
                }],
                'generationConfig': {
                    'temperature': 0.1,
                    'topK': 10,
                    'topP': 0.95,
                    'maxOutputTokens': 50,
                }
            }
            
            response = requests.post(
                self.vision_url,
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    barcode_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # Validate barcode format
                    barcode = re.sub(r'[^\d]', '', barcode_text)
                    if len(barcode) in [12, 13, 8]:  # Common barcode lengths
                        return barcode
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting barcode: {str(e)}")
            return None
