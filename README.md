# 🍎 Worldwide Food Product Scanner App

A production-grade, AI-powered food product scanner system combining a robust **Python Flask Backend** (leveraging Tesseract OCR, pyzbar, and Gemini 2.5 Flash AI) with a premium **Flutter Mobile Application** featuring offline caching, scan history, favorites, and real-time allergen/dietary warning alerts.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![Flutter](https://img.shields.io/badge/Flutter-3.0+-cyan.svg)](https://flutter.dev/)
[![Vercel Deployment](https://img.shields.io/badge/Vercel-Deployed-black.svg)](https://food-product-scanner-main.vercel.app)
[![Gemini AI](https://img.shields.io/badge/Gemini-2.5%20Flash-orange.svg)](https://deepmind.google/technologies/gemini/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌟 Key Features

### 1. Multi-Platform Scanning Options
* **Web Dashboard**: HTML5 browser-based camera scanning utilizing `html5-qrcode`, as well as drag-and-drop file uploads.
* **Flutter Mobile App**: Real-time camera scanning via `mobile_scanner`, featuring a manual barcode lookup and emulator-friendly test buttons.

### 2. Category-Aware Nutri-Score (FSA-NPS 2023+ Updated)
* Auto-detects product categories (Beverages, Cheese, Red Meat, Fats/Oils/Nuts, and General Foods) from Open Food Facts `categories_tags`.
* Implements official category-specific logic:
  - **Red Meat**: Hard cap of `2` points on positive protein contribution.
  - **Cheese**: Bypass negative points limit ($\ge 11$) to ensure protein is always counted.

### 3. Allergen & Dietary Alert System
* User profile configurations for dietary requirements (Vegan, Vegetarian) and common allergens (Gluten, Dairy, Peanuts, Nuts, Eggs, Soy, Fish, Shellfish).
* Real-time warning checks on scans displaying prominent warning banners if violations are detected.

### 4. Offline-Friendly Caching & Favorites
* Persists scan history and favorite product logs locally on mobile devices using `shared_preferences` for offline lookup.

### 5. AI-Powered Expert Analysis
* Integrated Gemini 2.5 Flash API to parse raw ingredients list, analyze health impacts, compile health benefits, and output storage/consumption advice.

---

## 📂 Project Architecture

```text
├── app.py                     # Flask web server & REST API endpoints
├── food_scanner.py            # OCR, barcode processing, and Gemini AI pipeline
├── nutriscore.py              # Category-aware Nutri-Score calculation module
├── product_database.py        # Open Food Facts API client
├── config.py                  # Environment config resolver
├── requirements.txt           # Python backend dependencies
├── Dockerfile                 # Backend containerization Dockerfile
├── docker-compose.yml         # Containerized development composer
├── static/ & templates/       # Web dashboard assets and markup
├── food_scanner_mobile/       # Flutter Mobile Application
│   ├── pubspec.yaml           # Flutter packages config
│   ├── lib/
│   │   ├── main.dart          # Mobile app boots & bottom nav shell
│   │   ├── models/            # Product JSON parsers
│   │   ├── services/          # Local persistence (SharedPreferences) & API clients
│   │   ├── widgets/           # Nutri-Score graphic badges
│   │   └── screens/           # Scan, Search, History, and Profile views
│   └── README.md              # Flutter installation guide
├── GCP_DEPLOY_GUIDE.md        # Cloud Run hosting instructions
└── GITHUB_PUSH_GUIDE.md       # Git version control push manual
```

---

## 🚀 Local Installation & Setup

### Part A: Python Flask Backend

1. **Clone the repository and enter the directory**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/worldwide-food-scanner.git
   cd worldwide-food-scanner
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate       # On Linux/macOS
   # venv\Scripts\activate        # On Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If running OCR locally, make sure to install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) on your system.*

4. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your Google Gemini AI API key:
   ```bash
   copy .env.example .env          # Windows
   # cp .env.example .env          # Linux/macOS
   ```
   Edit `.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Start Flask Server**:
   ```bash
   python app.py
   ```
   Open your browser to `http://localhost:5000` to view the web dashboard.

---

### Part B: Flutter Mobile Application

1. **Enter the mobile project directory**:
   ```bash
   cd food_scanner_mobile
   ```

2. **Fetch Flutter Dependencies**:
   ```bash
   flutter pub get
   ```

3. **Configure API Endpoint**:
   Open `lib/services/api_service.dart`. By default, it is configured for the Android Emulator (`http://10.0.2.2:5000`). If testing on iOS Simulator, update to `http://localhost:5000`.

4. **Run the App**:
   Launch your emulator and execute:
   ```bash
   flutter run
   ```
   *Tip: Use the **Quick Simulator** buttons on the Scan tab to easily test results without a physical camera.*

---

## 🐳 Containerization with Docker

You can run the backend services in an isolated environment with Tesseract, OpenCV, and ZBar pre-installed:

```bash
# Build and run using Docker Compose
docker-compose up --build -d

# Check runtime logs
docker-compose logs -f

# Shut down container
docker-compose down
```

---

## 🌐 Deploying the Backend

### Option 1: Vercel Serverless (Basic Hosting)
The backend is configured for Vercel using [vercel.json](vercel.json).
* **Live Deployment**: [https://food-product-scanner-main.vercel.app](https://food-product-scanner-main.vercel.app)
* *Note: Vercel is best suited for dashboard serving and manual calculation routes. Tesseract OCR and Barcode decoding are not supported on Vercel due to system binary restrictions.*

### Option 2: Google Cloud Run (Recommended for Full Features)
Deploy the containerized backend to Google Cloud Run to enable full image scanning and OCR capabilities:
1. Ensure the `gcloud` CLI is logged in.
2. Run the deployment script:
   ```bash
   ./deploy_gcp.sh      # On Linux/macOS
   # deploy_gcp.bat     # On Windows
   ```
3. Set your `GEMINI_API_KEY` under the Cloud Run Service Variables tab in the Google Cloud Console.
4. For step-by-step instructions, see the [GCP Deployment Guide](GCP_DEPLOY_GUIDE.md).

---

## 📄 License
This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
