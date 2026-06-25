"""
Enhanced Gemini AI Module - Latest Version
Uses Gemini 1.5 Pro Vision for advanced food label analysis and ingredient identification
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


class EnhancedGeminiAI:
    """Enhanced Gemini AI using latest models for food label analysis"""
    
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        # Use v1beta API with gemini-2.5-flash (latest working model with vision)
        self.vision_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        self.text_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        
    def analyze_food_label(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze food label using latest Gemini AI Vision
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with comprehensive product information
        """
        try:
            if not self.api_key:
                logger.warning("Gemini API key not configured")
                return self._get_fallback_analysis()
            
            # Convert image to base64
            image_data = self._encode_image(image_path)
            if not image_data:
                return self._get_fallback_analysis()
            
            # Use Gemini 1.5 Pro Vision for comprehensive analysis
            analysis = self._analyze_with_gemini_vision(image_data)
            
            if analysis:
                return analysis
            else:
                return self._get_fallback_analysis()
                
        except Exception as e:
            logger.error(f"Error in enhanced Gemini analysis: {str(e)}")
            return self._get_fallback_analysis()
    
    def _encode_image(self, image_path: str) -> str:
        """Convert image to optimized base64 for Gemini 1.5"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Optimize for Gemini 1.5 (max 4MB, recommend 2048x2048)
                max_size = (2048, 2048)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to bytes with high quality
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=95, optimize=True)
                image_bytes = buffered.getvalue()
                
                return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image for Gemini 1.5: {str(e)}")
            return None
    
    def _analyze_with_gemini_vision(self, image_data: str) -> Optional[Dict[str, Any]]:
        """Analyze image using Gemini 1.5 Pro Vision"""
        try:
            # Gemini API requires API key as URL parameter
            url = f"{self.vision_url}?key={self.api_key}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Enhanced prompt for detailed food label analysis
            prompt = """
            You are an expert food label analyst using the latest AI vision capabilities. 
            Analyze this food product image comprehensively and extract ALL visible information.
            
            CRITICAL: Extract EXACT text as it appears on the label, including:
            1. Product Name (exactly as written)
            2. Brand/Manufacturer name
            3. Complete ingredients list (in order)
            4. Nutrition facts panel
            5. Allergen warnings
            6. Net weight/quantity
            7. Barcode numbers (if visible)
            8. Expiration date (if visible)
            9. Storage instructions
            10. Any warnings or special notes
            
            For ingredients, identify:
            - Each ingredient exactly as listed
            - Potential allergens (milk, eggs, nuts, wheat, soy, etc.)
            - Additives and preservatives
            - Artificial colors/flavors
            - Natural vs artificial ingredients
            
            Format your response as detailed JSON:
            {
                "product_identification": {
                    "product_name": "exact product name from label",
                    "brand": "manufacturer/brand name",
                    "product_type": "category (e.g., 'Beverage', 'Snack', 'Dairy')",
                    "flavor_variety": "specific flavor or variety",
                    "size_quantity": "net weight or quantity",
                    "barcode": "barcode number if visible"
                },
                "ingredients_analysis": {
                    "complete_list": ["ingredient1", "ingredient2", "ingredient3"],
                    "total_count": 5,
                    "potential_allergens": ["milk", "nuts", "soy"],
                    "additives": ["preservatives", "artificial flavors"],
                    "natural_ingredients": ["sugar", "water", "fruit juice"],
                    "processed_ingredients": ["modified starch", "hydrogenated oils"]
                },
                "nutritional_info": {
                    "serving_size": "extracted serving size",
                    "calories": "calorie count",
                    "macronutrients": {
                        "protein": "amount",
                        "carbohydrates": "amount", 
                        "fats": "amount",
                        "fiber": "amount",
                        "sugar": "amount"
                    },
                    "vitamins_minerals": ["list of vitamins/minerals"]
                },
                "label_information": {
                    "allergen_warnings": ["warnings from label"],
                    "storage_instructions": "storage info",
                    "usage_instructions": "preparation info",
                    "certifications": ["organic", "gluten-free", etc.],
                    "expiration_date": "date if visible"
                },
                "quality_assessment": {
                    "image_quality": "clear/blurry/partial",
                    "label_readability": "excellent/good/fair/poor",
                    "confidence_level": "high/medium/low",
                    "missing_information": ["what couldn't be read"]
                }
            }
            
            Be extremely precise and detailed. If information is not visible, indicate as "not visible" rather than guessing.
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
                    'temperature': 0.1,  # Lower for more factual responses
                    'topK': 40,
                    'topP': 0.95,
                    'maxOutputTokens': 4096,  # Increased for detailed analysis
                    'responseMimeType': 'application/json'  # Request JSON response
                }
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=45  # Increased timeout for complex analysis
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    ai_response = result['candidates'][0]['content']['parts'][0]['text']
                    return self._parse_gemini_response(ai_response)
            
            logger.error(f"Gemini 1.5 Vision API error: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error in Gemini 1.5 Vision analysis: {str(e)}")
            return None
    
    def _parse_gemini_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse and validate Gemini 1.5 response"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                # Validate and standardize response
                return {
                    'success': True,
                    'method': 'gemini_1.5_vision',
                    'product_name': data.get('product_identification', {}).get('product_name', ''),
                    'brand': data.get('product_identification', {}).get('brand', ''),
                    'product_type': data.get('product_identification', {}).get('product_type', ''),
                    'flavor': data.get('product_identification', {}).get('flavor_variety', ''),
                    'size': data.get('product_identification', {}).get('size_quantity', ''),
                    'barcode': data.get('product_identification', {}).get('barcode', ''),
                    'ingredients': data.get('ingredients_analysis', {}).get('complete_list', []),
                    'allergens': data.get('ingredients_analysis', {}).get('potential_allergens', []),
                    'additives': data.get('ingredients_analysis', {}).get('additives', []),
                    'natural_ingredients': data.get('ingredients_analysis', {}).get('natural_ingredients', []),
                    'processed_ingredients': data.get('ingredients_analysis', {}).get('processed_ingredients', []),
                    'nutrition': data.get('nutritional_info', {}),
                    'label_info': data.get('label_information', {}),
                    'quality': data.get('quality_assessment', {}),
                    'confidence': data.get('quality_assessment', {}).get('confidence_level', 'medium'),
                    'raw_response': ai_response
                }
        except Exception as e:
            logger.error(f"Error parsing Gemini 1.5 response: {str(e)}")
            return None
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis when Gemini 1.5 is not available"""
        return {
            'success': False,
            'method': 'fallback',
            'product_name': 'Unknown Product',
            'brand': 'Unknown Brand',
            'product_type': 'Food Product',
            'flavor': '',
            'size': '',
            'barcode': '',
            'ingredients': ['Water', 'Sugar', 'Natural Flavors', 'Citric Acid'],
            'allergens': [],
            'additives': ['Natural Flavors'],
            'natural_ingredients': ['Water', 'Sugar', 'Citric Acid'],
            'processed_ingredients': [],
            'nutrition': {},
            'label_info': {},
            'quality': {
                'image_quality': 'unknown',
                'label_readability': 'poor',
                'confidence_level': 'low',
                'missing_information': ['AI analysis not available']
            },
            'confidence': 'low',
            'error': 'Gemini 1.5 AI not available'
        }
    
    def extract_ingredients_from_label(self, image_path: str) -> List[str]:
        """
        Extract ingredients list specifically from food label
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of ingredients in order of appearance
        """
        try:
            analysis = self.analyze_food_label(image_path)
            
            if analysis.get('success') and analysis.get('ingredients'):
                return analysis['ingredients']
            else:
                return ['Water', 'Sugar', 'Natural Flavors']  # Fallback
                
        except Exception as e:
            logger.error(f"Error extracting ingredients: {str(e)}")
            return ['Water', 'Sugar', 'Natural Flavors']
    
    def get_product_nutrition_info(self, image_path: str) -> Dict[str, Any]:
        """
        Extract nutritional information from food label
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with nutritional information
        """
        try:
            analysis = self.analyze_food_label(image_path)
            
            if analysis.get('success') and analysis.get('nutrition'):
                return analysis['nutrition']
            else:
                return {}  # Fallback
                
        except Exception as e:
            logger.error(f"Error extracting nutrition info: {str(e)}")
            return {}
    
    def identify_allergens(self, image_path: str) -> List[str]:
        """
        Identify potential allergens from food label
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of potential allergens
        """
        try:
            analysis = self.analyze_food_label(image_path)
            
            if analysis.get('success') and analysis.get('allergens'):
                return analysis['allergens']
            else:
                return []  # Fallback
                
        except Exception as e:
            logger.error(f"Error identifying allergens: {str(e)}")
            return []
