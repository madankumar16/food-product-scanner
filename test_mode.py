"""
Test mode for Food Product Scanner - works without camera
"""

import numpy as np
from food_scanner import (
    scanFoodProduct, ProductDatabase, ProductData,
    IngredientNormalizer, IngredientClassifier, HealthAnalyzer,
    SafetyCalculator, PDFGenerator, Dashboard, VegStatus, SafetyColor
)
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MockCamera:
    """Mock camera for testing"""
    
    def activate(self):
        logger.info("Mock camera activated")
    
    def capture(self):
        # Return a dummy image array
        return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def release(self):
        logger.info("Mock camera released")


def scanFoodProductTest(product_name: str = None, barcode: str = None, 
                       ingredients: list = None) -> Dict[str, Any]:
    """
    Test version of scanFoodProduct that doesn't require camera.
    Can be used with predefined product data.
    
    Args:
        product_name: Product name (optional)
        barcode: Barcode string (optional)
        ingredients: List of ingredient strings (optional)
        
    Returns:
        Dictionary containing dashboard data and PDF report
    """
    import time
    from food_scanner import (
        BarcodeDetector, OCR, IngredientNormalizer, IngredientClassifier,
        HealthAnalyzer, SafetyCalculator, PDFGenerator, Dashboard,
        VegStatus, SafetyColor, ClassifiedIngredient, HealthRisk
    )
    
    START_TIME = time.time()
    
    # Initialize components
    product_db = ProductDatabase()
    normalizer = IngredientNormalizer()
    classifier = IngredientClassifier()
    health_analyzer = HealthAnalyzer()
    safety_calc = SafetyCalculator()
    pdf_gen = PDFGenerator()
    
    try:
        # Get product data
        if barcode:
            product_data = product_db.fetch_by_barcode(barcode)
        elif ingredients:
            product_data = ProductData(
                name=product_name or "Test Product",
                brand="Test Brand",
                ingredients=ingredients
            )
        else:
            # Use sample data
            product_data = ProductData(
                name="Sample Cola Drink",
                brand="ColaBrand",
                ingredients=["Carbonated Water", "Sugar", "Caramel Color", 
                           "Phosphoric Acid", "Natural Flavors", "Caffeine"]
            )
        
        if product_data is None:
            raise ValueError("Product not found")
        
        # Continue with normal processing
        product_name = product_data.name
        brand_name = product_data.brand
        ingredient_list = product_data.ingredients
        
        # Normalize ingredients
        normalized_ingredients = []
        for ingredient in ingredient_list:
            normalized = normalizer.normalize(ingredient)
            normalized_ingredients.append(normalized)
        
        # Classify ingredients
        classified_ingredients = []
        for ingredient in normalized_ingredients:
            category = classifier.classify(ingredient)
            is_animal = classifier.is_animal_derived(ingredient)
            is_vegan_restricted = classifier.is_vegan_restricted(ingredient)
            
            classified_ing = ClassifiedIngredient(
                name=ingredient,
                category=category,
                is_animal_derived=is_animal,
                is_vegan_restricted=is_vegan_restricted
            )
            classified_ingredients.append(classified_ing)
        
        # Veg status check
        veg_status = VegStatus.VEGETARIAN
        has_animal_derived = False
        has_dairy_egg = False
        
        for ingredient in classified_ingredients:
            if ingredient.is_animal_derived:
                veg_status = VegStatus.NON_VEGETARIAN
                has_animal_derived = True
                break
            elif ingredient.is_vegan_restricted:
                has_dairy_egg = True
        
        if not has_animal_derived and not has_dairy_egg:
            veg_status = VegStatus.VEGAN
        
        # Health impact analysis
        health_risks = []
        for ingredient in classified_ingredients:
            risks = health_analyzer.analyze(ingredient.name)
            if risks:
                health_risk = HealthRisk(
                    ingredient=ingredient.name,
                    conditions=risks
                )
                health_risks.append(health_risk)
        
        # Safety threshold check
        exceeded_limits = []
        high_risk_detected = False
        for ingredient in classified_ingredients:
            if ingredient.quantity > ingredient.safe_limit:
                exceeded_limits.append(ingredient.name)
                high_risk_detected = True
        
        # Safety rating
        safety_color = safety_calc.determine_color(
            health_risks, exceeded_limits, high_risk_detected
        )
        
        from food_scanner import IngredientCategory
        harmful_count = len([ing for ing in classified_ingredients 
                           if ing.category != IngredientCategory.NATURAL])
        safety_score = safety_calc.calculate_score(
            len(classified_ingredients),
            harmful_count,
            len(exceeded_limits)
        )
        
        # Dashboard
        dashboard = Dashboard(
            product_name=product_name,
            brand=brand_name,
            veg_status=veg_status,
            ingredients=classified_ingredients,
            health_warnings=health_risks,
            safety_color=safety_color,
            safety_score=safety_score,
            exceeded_limits=exceeded_limits
        )
        
        # PDF generation
        pdf_report = pdf_gen.generate(dashboard, format="A4")
        
        # Performance check
        execution_time = time.time() - START_TIME
        logger.info(f"Execution time: {execution_time:.3f}s")
        
        if execution_time > 1.0:
            logger.warning(f"Performance warning: Execution took {execution_time:.3f}s")
        
        # Return result
        return {
            "dashboard": {
                "Product Name": dashboard.product_name,
                "Brand": dashboard.brand,
                "Veg Status": dashboard.veg_status.value,
                "Ingredients": [
                    {
                        "name": ing.name,
                        "category": ing.category.value
                    } for ing in dashboard.ingredients
                ],
                "Health Warnings": [
                    {
                        "ingredient": risk.ingredient,
                        "conditions": risk.conditions
                    } for risk in dashboard.health_warnings
                ],
                "Safety Color": dashboard.safety_color.value,
                "Safety Score": round(dashboard.safety_score, 2),
                "Exceeded Limits": dashboard.exceeded_limits
            },
            "pdf": pdf_report,
            "execution_time": round(execution_time, 3)
        }
    
    except Exception as e:
        logger.error(f"Error in scanFoodProductTest: {str(e)}")
        raise


if __name__ == "__main__":
    # Test with sample data
    print("Testing Food Product Scanner (Test Mode)")
    print("=" * 60)
    
    # Test 1: Sample cola drink
    print("\nTest 1: Cola Drink")
    result1 = scanFoodProductTest(
        ingredients=["Carbonated Water", "Sugar", "Caramel Color", 
                    "Phosphoric Acid", "Natural Flavors", "Caffeine"]
    )
    print(f"Product: {result1['dashboard']['Product Name']}")
    print(f"Safety: {result1['dashboard']['Safety Color']} ({result1['dashboard']['Safety Score']})")
    print(f"Veg Status: {result1['dashboard']['Veg Status']}")
    
    # Test 2: Energy bar with dairy
    print("\nTest 2: Energy Bar (with dairy)")
    result2 = scanFoodProductTest(
        ingredients=["Oats", "Honey", "Almonds", "Chocolate Chips", "Milk", "Vanilla Extract"]
    )
    print(f"Product: {result2['dashboard']['Product Name']}")
    print(f"Safety: {result2['dashboard']['Safety Color']} ({result2['dashboard']['Safety Score']})")
    print(f"Veg Status: {result2['dashboard']['Veg Status']}")
    
    # Test 3: Vegan product
    print("\nTest 3: Vegan Product")
    result3 = scanFoodProductTest(
        ingredients=["Water", "Organic Sugar", "Lemon Juice", "Natural Flavors"]
    )
    print(f"Product: {result3['dashboard']['Product Name']}")
    print(f"Safety: {result3['dashboard']['Safety Color']} ({result3['dashboard']['Safety Score']})")
    print(f"Veg Status: {result3['dashboard']['Veg Status']}")

