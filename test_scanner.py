"""
Test script to verify the food scanner is working properly
"""

import os
import sys

# Force UTF-8 encoding for stdout and stderr to handle emojis on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("=" * 60)
print("FOOD SCANNER DIAGNOSTIC TEST")
print("=" * 60)

# Test 1: Check imports
print("\n1. Testing imports...")
try:
    from food_scanner import scanFoodProductSmart
    print("   ✓ food_scanner imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import food_scanner: {e}")
    sys.exit(1)

try:
    from config import Config
    print("   ✓ config imported successfully")
    print(f"   ✓ Gemini API Key configured: {Config.GEMINI_API_KEY[:20]}..." if Config.GEMINI_API_KEY else "   ✗ No API key")
except Exception as e:
    print(f"   ✗ Failed to import config: {e}")

# Test 2: Check Gemini AI modules
print("\n2. Testing Gemini AI modules...")
try:
    from gemini_25_ai import Gemini25AI
    print("   ✓ Gemini 2.5 AI module available")
except Exception as e:
    print(f"   ✗ Gemini 2.5 AI not available: {e}")

try:
    from enhanced_gemini_ai import EnhancedGeminiAI
    print("   ✓ Enhanced Gemini AI module available")
except Exception as e:
    print(f"   ✗ Enhanced Gemini AI not available: {e}")

try:
    from gemini_ai import GeminiAI
    print("   ✓ Gemini AI module available")
except Exception as e:
    print(f"   ✗ Gemini AI not available: {e}")

# Test 3: Test scanner without image (should return error fallback)
print("\n3. Testing scanner without image...")
try:
    result = scanFoodProductSmart()
    print(f"   ✓ Scanner executed")
    print(f"   Product: {result['dashboard']['Product Name']}")
    print(f"   Brand: {result['dashboard']['Brand']}")
    print(f"   Safety: {result['dashboard']['Safety Color']} ({result['dashboard']['Safety Score']}/100)")
    print(f"   AI Method: {result.get('smart_features', {}).get('ai_method', 'unknown')}")
except Exception as e:
    print(f"   ✗ Scanner failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check if test image exists
print("\n4. Checking for test images...")
test_images = []
for ext in ['jpg', 'jpeg', 'png']:
    for name in ['test', 'sample', 'product', 'food']:
        filename = f"{name}.{ext}"
        if os.path.exists(filename):
            test_images.append(filename)
            print(f"   ✓ Found: {filename}")

if not test_images:
    print("   ℹ No test images found in current directory")
    print("   ℹ To test with an image, place a food product image in the project folder")

# Test 5: Test with image if available
if test_images:
    print(f"\n5. Testing scanner with image: {test_images[0]}...")
    try:
        result = scanFoodProductSmart(test_images[0])
        print(f"   ✓ Scanner executed with image")
        print(f"   Product: {result['dashboard']['Product Name']}")
        print(f"   Brand: {result['dashboard']['Brand']}")
        print(f"   Safety: {result['dashboard']['Safety Color']} ({result['dashboard']['Safety Score']}/100)")
        print(f"   Ingredients: {len(result['dashboard']['Ingredients'])} found")
        print(f"   AI Method: {result.get('smart_features', {}).get('ai_method', 'unknown')}")
        print(f"   Confidence: {result.get('smart_features', {}).get('confidence', 'unknown')}")
    except Exception as e:
        print(f"   ✗ Scanner failed with image: {e}")
        import traceback
        traceback.print_exc()

# Test 6: Check Flask app
print("\n6. Testing Flask app configuration...")
try:
    from app import app
    print("   ✓ Flask app imported successfully")
    print(f"   ✓ Debug mode: {app.config.get('DEBUG', False)}")
    print(f"   ✓ Secret key configured: {'Yes' if app.secret_key else 'No'}")
except Exception as e:
    print(f"   ✗ Failed to import Flask app: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC TEST COMPLETE")
print("=" * 60)
print("\nRECOMMENDATIONS:")
print("1. Ensure Gemini API key is valid")
print("2. Upload a clear food product label image")
print("3. Make sure the image shows visible ingredients text")
print("4. Restart Flask app after any code changes")
print("5. Check browser console for JavaScript errors")
print("\nTo run the app: python app.py")
print("=" * 60)
