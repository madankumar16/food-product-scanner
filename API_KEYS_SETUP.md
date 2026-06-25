# API Keys Setup Guide

This guide explains how to configure API keys for the Food Product Scanner application.

## Configuration Methods

### Method 1: Environment Variables (Recommended)

Set environment variables in your system or use a `.env` file:

```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your-gemini-api-key-here"
$env:USDA_API_KEY="your-api-key-here"
$env:SPOONACULAR_API_KEY="your-api-key-here"
$env:EDAMAM_API_KEY="your-edamam-api-key-here"
$env:EDAMAM_APP_ID="your-edamam-app-id-here"

# Linux/Mac
export GEMINI_API_KEY="your-gemini-api-key-here"
export USDA_API_KEY="your-api-key-here"
export SPOONACULAR_API_KEY="your-api-key-here"
export EDAMAM_API_KEY="your-edamam-api-key-here"
export EDAMAM_APP_ID="your-edamam-app-id-here"
```

### Method 2: .env File

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```
   GEMINI_API_KEY=your-gemini-api-key-here
   USDA_API_KEY=your-usda-api-key-here
   SPOONACULAR_API_KEY=your-spoonacular-api-key-here
   EDAMAM_API_KEY=your-edamam-api-key-here
   EDAMAM_APP_ID=your-edamam-app-id-here
   ```

3. Install python-dotenv (optional):
   ```bash
   pip install python-dotenv
   ```

4. Update `app.py` to load .env file:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Method 3: Direct Configuration

Edit `config.py` directly and add your API keys:

```python
USDA_API_KEY = "your-api-key-here"
SPOONACULAR_API_KEY = "your-api-key-here"
```

⚠️ **Warning**: Never commit API keys to version control!

## Available APIs

### 1. Open Food Facts API
- **Status**: ✅ No API key required
- **URL**: https://world.openfoodfacts.org/
- **Usage**: Automatically used for barcode lookups
- **Optional**: Set `OPENFOODFACTS_USER_AGENT` in config

### 2. USDA Food Data Central API
- **Status**: 🔑 API key required
- **Get Key**: https://fdc.nal.usda.gov/api-guide.html
- **Environment Variable**: `USDA_API_KEY`
- **Usage**: For detailed nutrition information

### 3. Spoonacular API
- **Status**: 🔑 API key required
- **Get Key**: https://spoonacular.com/food-api
- **Environment Variable**: `SPOONACULAR_API_KEY`
- **Usage**: For nutrition analysis and recipe data

### 4. Edamam Food Database API
- **Status**: 🔑 API key and App ID required
- **Get Key**: https://developer.edamam.com/
- **Environment Variables**: 
  - `EDAMAM_API_KEY`
  - `EDAMAM_APP_ID`
- **Usage**: For food database and nutrition data

## Current Implementation

The application currently uses:
- ✅ **Open Food Facts API** - No key required, automatically integrated
- ⚠️ **Other APIs** - Ready for integration, add keys to enable

## Testing API Keys

To test if your API keys are working, you can check in Python:

```python
from config import Config

# Check if API key is set
if Config.has_api_key('USDA'):
    print("USDA API key is configured")
    print(f"Key: {Config.get_api_key('USDA')[:10]}...")
else:
    print("USDA API key not found")
```

## Security Best Practices

1. **Never commit API keys** to Git
2. **Use environment variables** for sensitive data
3. **Rotate keys regularly** if compromised
4. **Use different keys** for development and production
5. **Restrict API key permissions** when possible
6. **Monitor API usage** to detect abuse

## Troubleshooting

### API Key Not Working
- Verify the key is correctly set in environment variables
- Check for extra spaces or quotes in the key
- Ensure the API key has proper permissions
- Check API service status

### Module Not Found
- Install required packages: `pip install requests`
- For .env support: `pip install python-dotenv`

### API Rate Limits
- Most APIs have rate limits
- Implement caching for frequently accessed data
- Consider upgrading API plan if needed

## Next Steps

1. Get API keys from the services you want to use
2. Add them to your `.env` file or environment variables
3. Restart the application
4. Test the integration

For more information, see the main README.md file.


