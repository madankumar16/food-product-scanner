"""
Gemini AI Integration for Food Product Scanner
"""

import logging
import requests
import json
from typing import Dict, List, Any
import re

# Import configuration
try:
    from config import Config
except ImportError:
    class Config:
        GEMINI_API_KEY = None

logger = logging.getLogger(__name__)

class GeminiAI:
    """Gemini AI integration for enhanced product analysis"""
    
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY or self._get_api_key_from_env()
        # Use v1beta API with gemini-2.5-flash (latest working model)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        
    def _get_api_key_from_env(self):
        """Get API key from environment variables"""
        import os
        return os.getenv('GEMINI_API_KEY')
    
    def analyze_product(self, product_name: str, brand: str, ingredients: List[str], safety_score: int) -> Dict[str, Any]:
        """
        Analyze product using Gemini AI for enhanced insights
        
        Args:
            product_name: Name of the product
            brand: Brand of the product
            ingredients: List of ingredients
            safety_score: Current safety score
            
        Returns:
            Dictionary containing AI analysis
        """
        try:
            if not self.api_key:
                logger.warning("Gemini API key not configured")
                return self._get_fallback_analysis(product_name, brand, ingredients, safety_score)
            
            # Create prompt for Gemini
            prompt = self._create_analysis_prompt(product_name, brand, ingredients, safety_score)
            
            # Make request to Gemini API
            # Gemini API requires API key as URL parameter
            url = f"{self.base_url}?key={self.api_key}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            data = {
                'contents': [{
                    'parts': [{
                        'text': prompt
                    }]
                }],
                'generationConfig': {
                    'temperature': 0.1,  # Low temperature for maximum compliance
                    'topK': 40,
                    'topP': 0.95,
                    'maxOutputTokens': 2048,
                    'responseMimeType': 'application/json'
                }
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    ai_response = result['candidates'][0]['content']['parts'][0]['text']
                    return self._parse_ai_response(ai_response)
            
            logger.error(f"Gemini API error: {response.status_code} - {response.text}")
            return self._get_fallback_analysis(product_name, brand, ingredients, safety_score)
            
        except Exception as e:
            logger.error(f"Error in Gemini AI analysis: {str(e)}")
            return self._get_fallback_analysis(product_name, brand, ingredients, safety_score)
    
    def _create_analysis_prompt(self, product_name: str, brand: str, ingredients: List[str], safety_score: int) -> str:
        """Create comprehensive prompt for product analysis"""
        ingredients_str = ", ".join(ingredients[:20])  # Limit to first 20 ingredients
        
        prompt = f"""
        As a food safety expert and nutritionist, please analyze this food product comprehensively:

        PRODUCT DETAILS:
        - Product Name: {product_name}
        - Brand: {brand}
        - Ingredients: {ingredients_str}
        - Current Safety Score: {safety_score}/100

        Please provide a detailed analysis including:
        1. Product category and type
        2. Nutritional insights based on ingredients
        3. Potential allergens and sensitivities
        4. Health benefits and concerns
        5. Recommended consumption guidelines
        6. Suitable dietary preferences (vegan, vegetarian, etc.)
        7. Storage and usage recommendations
        8. Comparison to similar products
        9. Overall health impact assessment

        Format your response as JSON with the following structure:
        {{
            "product_category": "category of the product",
            "nutritional_insights": ["insight 1", "insight 2"],
            "allergens": ["allergen 1", "allergen 2"],
            "health_benefits": ["benefit 1", "benefit 2"],
            "health_concerns": ["concern 1", "concern 2"],
            "consumption_guidelines": "guidelines text",
            "dietary_suitability": {{
                "vegan": true/false,
                "vegetarian": true/false,
                "gluten_free": true/false,
                "dairy_free": true/false
            }},
            "storage_recommendations": "storage advice",
            "usage_recommendations": "usage advice",
            "similar_products": ["product 1", "product 2"],
            "health_impact": "overall health impact",
            "expert_summary": "comprehensive summary"
        }}

        Be thorough, accurate, and provide actionable insights.
        """
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data"""
        try:
            # Clean potential markdown wrapping
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Try to load directly
            try:
                return json.loads(cleaned_response)
            except json.JSONDecodeError:
                pass
                
            # Try to extract JSON using regex
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                return self._create_structured_response_from_text(ai_response)
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return self._create_structured_response_from_text(ai_response)
    
    def _create_structured_response_from_text(self, text: str) -> Dict[str, Any]:
        """Create structured response from unstructured text"""
        return {
            "product_category": "Processed Food",
            "nutritional_insights": ["AI analysis available"],
            "allergens": ["Check ingredients list"],
            "health_benefits": ["Product analysis completed"],
            "health_concerns": ["Review ingredients"],
            "consumption_guidelines": "Consume in moderation",
            "dietary_suitability": {
                "vegan": False,
                "vegetarian": True,
                "gluten_free": False,
                "dairy_free": False
            },
            "storage_recommendations": "Store according to package instructions",
            "usage_recommendations": "Use as directed",
            "similar_products": ["Similar products available"],
            "health_impact": "Moderate impact",
            "expert_summary": text[:500] if len(text) > 500 else text
        }
    
    def _get_fallback_analysis(self, product_name: str, brand: str, ingredients: List[str], safety_score: int) -> Dict[str, Any]:
        """Get fallback analysis when AI is not available"""
        return {
            "product_category": "Food Product",
            "nutritional_insights": [
                f"Contains {len(ingredients)} ingredients",
                f"Safety score: {safety_score}/100"
            ],
            "allergens": self._identify_common_allergens(ingredients),
            "health_benefits": ["Processed food analysis"],
            "health_concerns": ["Review ingredient list for personal sensitivities"],
            "consumption_guidelines": "Consume in moderation as part of balanced diet",
            "dietary_suitability": {
                "vegan": self._check_vegan_status(ingredients),
                "vegetarian": self._check_vegetarian_status(ingredients),
                "gluten_free": self._check_gluten_free(ingredients),
                "dairy_free": self._check_dairy_free(ingredients)
            },
            "storage_recommendations": "Store in cool, dry place",
            "usage_recommendations": "Use according to package instructions",
            "similar_products": ["Similar processed foods"],
            "health_impact": self._get_health_impact_level(safety_score),
            "expert_summary": f"{product_name} by {brand} is a processed food product with {len(ingredients)} ingredients. Safety score indicates {self._get_health_impact_level(safety_score)} health impact."
        }
    
    def _identify_common_allergens(self, ingredients: List[str]) -> List[str]:
        """Identify common allergens in ingredient list"""
        allergens = []
        common_allergens = {
            'milk': ['milk', 'whey', 'casein', 'lactose'],
            'eggs': ['egg', 'albumin'],
            'fish': ['fish', 'salmon', 'tuna', 'cod'],
            'shellfish': ['shrimp', 'crab', 'lobster'],
            'tree nuts': ['almond', 'walnut', 'cashew', 'pecan'],
            'peanuts': ['peanut', 'groundnut'],
            'wheat': ['wheat', 'gluten', 'flour'],
            'soy': ['soy', 'soybean', 'tofu'],
            'sesame': ['sesame', 'tahini']
        }
        
        ingredients_lower = [ing.lower() for ing in ingredients]
        
        for allergen, allergen_words in common_allergens.items():
            if any(allergen_word in ing for ing in ingredients_lower for allergen_word in allergen_words):
                allergens.append(allergen.capitalize())
        
        return list(set(allergens))
    
    def _check_vegan_status(self, ingredients: List[str]) -> bool:
        """Check if product is vegan"""
        non_vegan_ingredients = ['milk', 'egg', 'honey', 'gelatin', 'whey', 'casein']
        ingredients_lower = [ing.lower() for ing in ingredients]
        return not any(nv in ing for ing in ingredients_lower for nv in non_vegan_ingredients)
    
    def _check_vegetarian_status(self, ingredients: List[str]) -> bool:
        """Check if product is vegetarian"""
        non_veg_ingredients = ['meat', 'poultry', 'fish', 'gelatin']
        ingredients_lower = [ing.lower() for ing in ingredients]
        return not any(nv in ing for ing in ingredients_lower for nv in non_veg_ingredients)
    
    def _check_gluten_free(self, ingredients: List[str]) -> bool:
        """Check if product is gluten free"""
        gluten_ingredients = ['wheat', 'gluten', 'barley', 'rye', 'malt']
        ingredients_lower = [ing.lower() for ing in ingredients]
        return not any(g in ing for ing in ingredients_lower for g in gluten_ingredients)
    
    def _check_dairy_free(self, ingredients: List[str]) -> bool:
        """Check if product is dairy free"""
        dairy_ingredients = ['milk', 'whey', 'casein', 'lactose', 'cheese', 'butter']
        ingredients_lower = [ing.lower() for ing in ingredients]
        return not any(d in ing for ing in ingredients_lower for d in dairy_ingredients)
    
    def _get_health_impact_level(self, safety_score: int) -> str:
        """Get descriptive health impact level"""
        if safety_score >= 80:
            return "minimal health concerns"
        elif safety_score >= 60:
            return "moderate health impact"
        elif safety_score >= 40:
            return "significant health concerns"
        else:
            return "major health concerns"
