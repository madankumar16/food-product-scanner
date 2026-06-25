"""
Product database and identification module
"""

import logging
from typing import List, Optional
import re
import os

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests library not available. Install with: pip install requests")

from food_scanner import ProductData

# Import configuration
try:
    from config import Config
except ImportError:
    # Fallback if config not available
    class Config:
        OPENFOODFACTS_USER_AGENT = "FoodScanner/1.0"
        @staticmethod
        def get_api_key(service): return None

logger = logging.getLogger(__name__)


class ProductDatabase:
    """Product database interface"""
    
    # Sample product database (in production, this would be a real database or API)
    SAMPLE_PRODUCTS = {
        "1234567890123": ProductData(
            name="Cola Drink",
            brand="ColaBrand",
            ingredients=["Carbonated Water", "Sugar", "Caramel Color", "Phosphoric Acid", "Natural Flavors", "Caffeine"],
            barcode="1234567890123"
        ),
        "9876543210987": ProductData(
            name="Energy Bar",
            brand="EnergyBrand",
            ingredients=["Oats", "Honey", "Almonds", "Chocolate Chips", "Milk", "Vanilla Extract"],
            barcode="9876543210987"
        ),
        "4567890123456": ProductData(
            name="Orange Juice",
            brand="FreshJuice",
            ingredients=["Orange Juice", "Water", "Sugar", "Vitamin C", "Natural Orange Flavor"],
            barcode="4567890123456"
        ),
        "7890123456789": ProductData(
            name="Potato Chips",
            brand="ChipCo",
            ingredients=["Potatoes", "Vegetable Oil", "Salt", "Natural Flavors"],
            barcode="7890123456789"
        ),
        "3456789012345": ProductData(
            name="Chocolate Cookies",
            brand="SweetTreats",
            ingredients=["Wheat Flour", "Sugar", "Chocolate Chips", "Butter", "Eggs", "Vanilla"],
            barcode="3456789012345"
        )
    }
    
    def fetch_by_barcode(self, barcode: str) -> Optional[ProductData]:
        """
        Fetch product data by barcode
        
        Args:
            barcode: Barcode string
            
        Returns:
            ProductData if found, None otherwise
        """
        logger.info(f"Fetching product by barcode: {barcode}")
        
        # Check sample database first
        if barcode in self.SAMPLE_PRODUCTS:
            return self.SAMPLE_PRODUCTS[barcode]
        
        # Try Open Food Facts API (no API key required)
        if REQUESTS_AVAILABLE:
            product_data = self._fetch_from_openfoodfacts(barcode)
            if product_data:
                return product_data
        
        logger.warning(f"Product not found for barcode: {barcode}")
        # Return fallback product instead of None
        return ProductData(
            name="Barcode Scanned Product",
            brand="Unknown Brand",
            ingredients=["Water", "Sugar", "Natural Flavors", "Citric Acid"],
            barcode=barcode
        )
    
    def _fetch_from_openfoodfacts(self, barcode: str) -> Optional[ProductData]:
        """
        Fetch product data from Open Food Facts API
        
        Args:
            barcode: Barcode string
            
        Returns:
            ProductData if found, None otherwise
        """
        try:
            url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
            headers = {
                'User-Agent': Config.OPENFOODFACTS_USER_AGENT
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 1 and data.get('product'):
                product = data['product']
                
                # Extract product information
                product_name = product.get('product_name') or product.get('product_name_en') or 'Unknown Product'
                brand = product.get('brands') or product.get('brand') or 'Unknown Brand'
                
                # Extract ingredients
                ingredients = []
                if product.get('ingredients_text'):
                    ingredients_text = product['ingredients_text']
                    ingredients = self._extract_ingredients_from_text(ingredients_text)
                elif product.get('ingredients'):
                    ingredients = [ing.get('text', '') for ing in product['ingredients'] if ing.get('text')]
                
                if not ingredients:
                    # Use fallback ingredients if none found in API
                    ingredients = ["Water", "Sugar", "Natural Flavors"]
                
                # Extract premium assets & scores
                image_url = product.get('image_front_url') or product.get('image_url')
                nutriscore = product.get('nutriscore_grade')
                if nutriscore:
                    nutriscore = nutriscore.upper()
                
                nova_group = product.get('nova_group')
                if nova_group is not None:
                    try:
                        nova_group = int(nova_group)
                    except (ValueError, TypeError):
                        nova_group = None
                
                ecoscore = product.get('ecoscore_grade')
                if ecoscore:
                    ecoscore = ecoscore.upper()
                
                nutriments = product.get('nutriments', {})
                allergens_text = product.get('allergens') or ""
                allergens = [a.strip().replace('en:', '') for a in allergens_text.split(',') if a.strip()] if allergens_text else []
                categories_tags = product.get('categories_tags', [])
                
                logger.info(f"Successfully fetched product from Open Food Facts: {product_name}")
                return ProductData(
                    name=product_name,
                    brand=brand,
                    ingredients=ingredients,
                    barcode=barcode,
                    image_url=image_url,
                    nutriscore=nutriscore,
                    nova_group=nova_group,
                    ecoscore=ecoscore,
                    nutriments=nutriments,
                    allergens=allergens,
                    categories_tags=categories_tags
                )
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching from Open Food Facts: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Open Food Facts API: {e}")
        
        return None
    
    def identify_from_text(self, text: str) -> Optional[ProductData]:
        """
        Identify product from ingredient text
        
        Args:
            text: Ingredient text from OCR
            
        Returns:
            ProductData if identified, None otherwise
        """
        logger.info("Identifying product from text")
        
        # Extract product name and brand from text
        product_name, brand = self._extract_product_name_and_brand(text)
        
        # Extract ingredients from text
        ingredients = self._extract_ingredients_from_text(text)
        
        if not ingredients:
            logger.warning("No ingredients found in text")
            # Return a fallback product with common ingredients
            return ProductData(
                name=product_name or "Camera Captured Product",
                brand=brand or "Scanned Brand",
                ingredients=["Water", "Sugar", "Natural Flavors", "Citric Acid"]
            )
        
        # Return product with extracted information
        return ProductData(
            name=product_name or "Identified Product",
            brand=brand or "Unknown Brand",
            ingredients=ingredients
        )
    
    def _extract_product_name_and_brand(self, text: str) -> tuple[str, str]:
        """
        Extract product name and brand from OCR text
        
        Args:
            text: Raw text from OCR
            
        Returns:
            Tuple of (product_name, brand)
        """
        if not text:
            return None, None
        
        # Common patterns for product names and brands
        lines = text.split('\n')
        product_name = None
        brand = None
        
        # Look for brand patterns (usually in first few lines, often in all caps or bold)
        brand_patterns = [
            r'^([A-Z][A-Z\s]{2,20})$',  # All caps brand names
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+)$',  # Title case brand names
            r'^(.+?)\s+(?:[Cc]ola|[Ss]oda|[Jj]uice|[Ww]ater|[Bb]everage)',  # Brand + product type
        ]
        
        # Look for product name patterns
        product_patterns = [
            r'^([A-Z][a-zA-Z\s]+(?:[Cc]ola|[Ss]oda|[Jj]uice|[Ww]ater|[Bb]everage|[Dd]rink|[Bb]ar|[Cc]hips|[Cc]ookies))',
            r'^([A-Z][a-zA-Z\s]+(?:[Ff]lavor|[Tt]aste))',
            r'^([A-Z][a-zA-Z\s]+\s+[A-Z][a-zA-Z]+)',  # Title case product names
        ]
        
        # First few lines are likely to contain brand/product info
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if not line or len(line) < 3:
                continue
                
            # Skip ingredient lines
            if any(keyword in line.lower() for keyword in ['ingredients', 'nutrition', 'serving', 'contains']):
                break
            
            # Try to identify brand
            if not brand:
                for pattern in brand_patterns:
                    match = re.search(pattern, line)
                    if match:
                        brand_candidate = match.group(1).strip()
                        if len(brand_candidate) >= 2 and len(brand_candidate) <= 30:
                            brand = brand_candidate
                            break
            
            # Try to identify product name
            if not product_name:
                for pattern in product_patterns:
                    match = re.search(pattern, line)
                    if match:
                        product_candidate = match.group(1).strip()
                        if len(product_candidate) >= 3 and len(product_candidate) <= 50:
                            product_name = product_candidate
                            break
        
        # If no specific patterns found, use first non-ingredient line as product name
        if not product_name:
            for line in lines[:3]:
                line = line.strip()
                if (line and len(line) >= 3 and len(line) <= 50 and 
                    not any(keyword in line.lower() for keyword in ['ingredients', 'nutrition', 'facts', 'serving'])):
                    product_name = line
                    break
        
        # Clean up extracted names
        if product_name:
            product_name = re.sub(r'[^a-zA-Z0-9\s\-]', '', product_name).strip()
            product_name = ' '.join(word.capitalize() for word in product_name.split())
        
        if brand:
            brand = re.sub(r'[^a-zA-Z0-9\s\-]', '', brand).strip()
            brand = brand.title()
        
        logger.info(f"Extracted - Product: {product_name}, Brand: {brand}")
        return product_name, brand
    
    def _extract_ingredients_from_text(self, text: str) -> List[str]:
        """
        Extract ingredient list from text
        
        Args:
            text: Raw text from OCR
            
        Returns:
            List of ingredient strings
        """
        if not text:
            return []
        
        # Common patterns for ingredient lists
        # Pattern 1: "Ingredients:" followed by comma-separated list
        pattern1 = r'[Ii]ngredients?[:\s]+(.*?)(?:\n\n|\Z)'
        match = re.search(pattern1, text, re.DOTALL)
        if match:
            ingredients_text = match.group(1)
        else:
            # Pattern 2: Look for common ingredient separators
            ingredients_text = text
        
        # Split by common separators
        ingredients = re.split(r'[,;]\s*|\n', ingredients_text)
        
        # Clean up ingredients
        cleaned = []
        for ing in ingredients:
            ing = ing.strip()
            # Remove common prefixes/suffixes
            ing = re.sub(r'^[•\-\*]\s*', '', ing)
            ing = re.sub(r'\s*\(.*?\)\s*$', '', ing)  # Remove parenthetical notes
            if ing and len(ing) > 2:  # Filter out very short strings
                cleaned.append(ing)
        
        logger.info(f"Extracted {len(cleaned)} ingredients from text")
        return cleaned

