"""
Configuration file for API keys and settings
"""

import os
import sys
from typing import Optional
from pathlib import Path

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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    
    # Get the path to .env file
    env_path = Path('.') / '.env'
    
    # Load .env file if it exists
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print("✅ Loaded environment variables from .env file")
    else:
        print("⚠️  No .env file found, using default configuration")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("⚠️  Using default configuration")


class Config:
    """Application configuration"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # API Keys - Add your API keys here or set as environment variables
    # Open Food Facts API (no key required, but you can set user agent)
    OPENFOODFACTS_USER_AGENT = os.environ.get('OPENFOODFACTS_USER_AGENT') or 'FoodScanner/1.0'
    
    # Gemini AI API Key (REQUIRED for AI analysis)
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
    
    # Optional: Other product database APIs
    # USDA_API_KEY = os.environ.get('USDA_API_KEY') or ''
    # SPOONACULAR_API_KEY = os.environ.get('SPOONACULAR_API_KEY') or ''
    # EDAMAM_API_KEY = os.environ.get('EDAMAM_API_KEY') or ''
    # EDAMAM_APP_ID = os.environ.get('EDAMAM_APP_ID') or ''
    
    # Database Configuration (if using database)
    # DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///food_scanner.db'
    
    # Session Configuration
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    @staticmethod
    def get_api_key(service_name: str) -> Optional[str]:
        """
        Get API key for a service
        
        Args:
            service_name: Name of the service (e.g., 'USDA', 'SPOONACULAR')
            
        Returns:
            API key if available, None otherwise
        """
        env_key = f'{service_name}_API_KEY'
        return os.environ.get(env_key)
    
    @staticmethod
    def has_api_key(service_name: str) -> bool:
        """
        Check if API key is available for a service
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if API key exists, False otherwise
        """
        return Config.get_api_key(service_name) is not None

