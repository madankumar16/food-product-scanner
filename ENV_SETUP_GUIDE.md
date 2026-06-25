# 🔑 Environment Variables Setup Guide

## Overview
Your API keys are now stored in a `.env` file for better security and easier management.

---

## 📁 File Locations

### 1. `.env` (Your actual API keys - KEEP SECRET!)
**Location**: Root directory of the project
**Contains**: Your real API keys
**Status**: ✅ Already created with your Gemini API key
**Security**: ⚠️ Never commit to Git (already in .gitignore)

### 2. `.env.example` (Template file)
**Location**: Root directory of the project
**Contains**: Template with placeholder values
**Purpose**: Share with others without exposing your keys
**Security**: ✅ Safe to commit to Git

### 3. `config.py` (Configuration loader)
**Location**: Root directory of the project
**Purpose**: Loads environment variables from `.env` file
**Status**: ✅ Updated to use python-dotenv

---

## 🔍 Where is Your API Key?

### Current Setup:

**File**: `.env`
**Line**: 9
```env
GEMINI_API_KEY=AIzaSyCRyC1Q4HAVrUokb2-UK0dxaObeyHjEe0g
```

### How It Works:

1. **`.env` file** stores the API key
2. **`config.py`** loads it using `python-dotenv`
3. **All modules** access it via `Config.GEMINI_API_KEY`

---

## 📝 How to View/Edit Your API Key

### Option 1: Edit .env File Directly

**Windows:**
```cmd
notepad .env
```

**Or open in your code editor:**
- VS Code: Open `.env` file
- Any text editor: Open `.env` file

### Option 2: View in Terminal

**Windows:**
```cmd
type .env
```

### Option 3: Check in Python

```python
from config import Config
print(Config.GEMINI_API_KEY)
```

---

## 🔄 How to Change API Key

### Method 1: Edit .env File

1. Open `.env` file in text editor
2. Find line: `GEMINI_API_KEY=...`
3. Replace with your new key
4. Save file
5. Restart Flask app

### Method 2: Set Environment Variable (Temporary)

**Windows CMD:**
```cmd
set GEMINI_API_KEY=your-new-api-key
python app.py
```

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY="your-new-api-key"
python app.py
```

---

## 🆕 How to Get a New Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key
5. Paste in `.env` file:
   ```env
   GEMINI_API_KEY=your-new-key-here
   ```

---

## 📋 Complete .env File Structure

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True

# Gemini AI API Key (Required)
GEMINI_API_KEY=AIzaSyCRyC1Q4HAVrUokb2-UK0dxaObeyHjEe0g

# Open Food Facts API
OPENFOODFACTS_USER_AGENT=FoodScanner/1.0

# Optional APIs (uncomment if needed)
# USDA_API_KEY=your-key
# SPOONACULAR_API_KEY=your-key
# EDAMAM_API_KEY=your-key
# EDAMAM_APP_ID=your-id

# Database (optional)
# DATABASE_URL=sqlite:///food_scanner.db

# Session
SESSION_PERMANENT=True
PERMANENT_SESSION_LIFETIME=86400
```

---

## 🔒 Security Best Practices

### ✅ DO:
- Keep `.env` file in `.gitignore` (already done)
- Use `.env.example` for sharing templates
- Rotate API keys regularly
- Use different keys for development/production
- Set restrictive file permissions on `.env`

### ❌ DON'T:
- Commit `.env` to Git
- Share `.env` file publicly
- Hardcode API keys in code
- Use production keys in development
- Store keys in plain text elsewhere

---

## 🧪 Test Your Configuration

### Check if .env is loaded:
```cmd
python -c "from config import Config; print('API Key:', Config.GEMINI_API_KEY[:20] + '...')"
```

### Run diagnostic test:
```cmd
python test_scanner.py
```

**Expected output:**
```
✓ config imported successfully
✓ Gemini API Key configured: AIzaSyCRyC1Q4HAVrUok...
```

---

## 🚀 Quick Start

### First Time Setup:

1. **Install python-dotenv** (already done):
   ```cmd
   pip install python-dotenv
   ```

2. **Verify .env file exists**:
   ```cmd
   dir .env
   ```

3. **Check API key is loaded**:
   ```cmd
   python -c "from config import Config; print(Config.GEMINI_API_KEY[:20])"
   ```

4. **Run the app**:
   ```cmd
   python app.py
   ```

---

## 🔧 Troubleshooting

### Problem: "No .env file found"
**Solution**: Create `.env` file in project root
```cmd
copy .env.example .env
```
Then edit `.env` with your API key

### Problem: "python-dotenv not installed"
**Solution**: Install it
```cmd
pip install python-dotenv
```

### Problem: API key not loading
**Solution**: Check file location
```cmd
# .env should be in project root
dir .env

# Check if it's being loaded
python -c "from config import Config; print(Config.GEMINI_API_KEY)"
```

### Problem: "Module 'dotenv' not found"
**Solution**: Reinstall python-dotenv
```cmd
pip uninstall python-dotenv
pip install python-dotenv
```

---

## 📊 Environment Variable Priority

The app loads API keys in this order:

1. **Environment variables** (highest priority)
   - Set via `set GEMINI_API_KEY=...`
   
2. **`.env` file** (medium priority)
   - Loaded by python-dotenv
   
3. **Hardcoded default** (lowest priority)
   - Fallback in `config.py`

**Example:**
```python
# Priority order:
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')  # 1. Check environment
                 or load_from_dotenv()              # 2. Check .env file
                 or 'AIzaSy...'                     # 3. Use default
```

---

## 🌍 Deployment

### For Production:

**Don't use .env file in production!**

Instead, set environment variables directly:

**Heroku:**
```bash
heroku config:set GEMINI_API_KEY=your-key
```

**AWS:**
```bash
aws lambda update-function-configuration \
  --function-name food-scanner \
  --environment Variables={GEMINI_API_KEY=your-key}
```

**Docker:**
```dockerfile
ENV GEMINI_API_KEY=your-key
```

**Or use secrets management:**
- AWS Secrets Manager
- Google Cloud Secret Manager
- Azure Key Vault
- HashiCorp Vault

---

## 📝 Summary

### Your API Key Locations:

1. **Primary**: `.env` file (line 9)
   ```
   GEMINI_API_KEY=AIzaSyCRyC1Q4HAVrUokb2-UK0dxaObeyHjEe0g
   ```

2. **Backup**: `config.py` (line 35)
   ```python
   GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'AIzaSy...'
   ```

3. **Template**: `.env.example` (for sharing)
   ```
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

### Quick Commands:

**View API key:**
```cmd
type .env | findstr GEMINI
```

**Edit API key:**
```cmd
notepad .env
```

**Test API key:**
```cmd
python test_scanner.py
```

**Run app:**
```cmd
python app.py
```

---

## ✅ Checklist

- [x] `.env` file created
- [x] `.env.example` template created
- [x] `python-dotenv` installed
- [x] `config.py` updated to load .env
- [x] `.gitignore` includes .env
- [x] API key working
- [x] App running successfully

**Everything is set up correctly!** 🎉

---

*Last Updated: January 7, 2026*
*Status: ✅ Environment variables configured*
