# 🍎 Food Product Scanner

A comprehensive AI-powered food product analysis system that scans products, identifies ingredients, classifies them, and provides health impact assessments with safety ratings.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![Gemini AI](https://img.shields.io/badge/Gemini-2.5%20Flash-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### 🔍 Scanning Methods
- **📷 Live Camera Scan**: Real-time camera capture with live feed
- **📁 Image Upload**: Drag & drop or browse file upload
- **🖼️ Image Preview**: See selected images before scanning
- **📸 Instant Analysis**: Get results in 2-5 seconds

### 🤖 AI-Powered Analysis
- **🧠 Gemini 2.5 Flash AI**: Google's latest AI model
- **📊 Product Classification**: Automatic category detection
- **🌱 Dietary Analysis**: Vegan/Vegetarian/Gluten-Free status
- **⚠️ Allergen Detection**: Smart allergen identification
- **💪 Health Benefits**: Nutritional benefits analysis
- **🎯 Expert Recommendations**: Usage and storage guidelines

### 📊 Results & Reports
- **🎨 Beautiful Modal Display**: Professional results interface
- **📄 PDF Reports**: Downloadable comprehensive analysis
- **💾 Scan History**: Track all previous scans
- **📈 Safety Scoring**: Color-coded safety ratings (GREEN/YELLOW/RED)
- **⚠️ Health Warnings**: Detailed health concerns

### 🎨 UI/UX Features
- **🌟 Modern Design**: Clean white and light blue theme
- **📱 Responsive Layout**: Works on all devices
- **🔄 Smooth Animations**: Professional transitions
- **🎯 Intuitive Interface**: Easy to use
- **📊 Real-time Updates**: Live scanning feedback

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Tesseract OCR (optional, for enhanced text extraction)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/food-product-scanner.git
   cd food-product-scanner
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example file
   copy .env.example .env
   
   # Edit .env and add your Gemini API key
   # Get your API key from: https://makersuite.google.com/app/apikey
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   ```
   http://localhost:5000
   ```

## 🔑 API Keys Setup

### Gemini AI API Key (Required)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key
5. Add to `.env` file:
   ```env
   GEMINI_API_KEY=your-api-key-here
   ```

See [ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md) for detailed instructions.

## 📖 Usage

### Upload Image Method

1. Click "Upload Image" option
2. Drag & drop or browse for food product image
3. Click "Start Scan"
4. View comprehensive results in modal
5. Download PDF report (optional)

### Camera Method

1. Click "Camera Scan" option
2. Allow camera permission when prompted
3. Point camera at product label
4. Click "Capture & Scan"
5. View instant AI analysis

### Results Include

- Product name and brand
- Complete ingredients list
- Vegetarian/vegan status
- Safety rating (0-100 score)
- Health warnings
- Allergen information
- AI-powered recommendations
- Downloadable PDF report

## 🏗️ Project Structure

```
food-product-scanner/
├── app.py                      # Flask web application
├── food_scanner.py             # Core scanning logic
├── gemini_25_ai.py            # Gemini 2.5 Flash AI
├── enhanced_gemini_ai.py      # Enhanced AI module
├── gemini_ai.py               # AI analysis module
├── config.py                  # Configuration
├── camera_handler.py          # Camera interface
├── barcode_handler.py         # Barcode detection
├── ocr_handler.py             # Text extraction
├── pdf_generator.py           # PDF reports
├── product_database.py        # Product lookup
├── requirements.txt           # Dependencies
├── .env.example               # Environment template
├── templates/                 # HTML templates
│   ├── dashboard.html
│   ├── history.html
│   ├── profile.html
│   └── scan_details.html
├── static/                    # Static assets
│   ├── css/
│   └── js/
└── docs/                      # Documentation
```

## 🛠️ Technologies Used

### Backend
- **Flask** - Web framework
- **Gemini 2.5 Flash** - Google's AI model
- **OpenCV** - Image processing
- **ReportLab** - PDF generation
- **Pillow** - Image handling
- **python-dotenv** - Environment variables

### Frontend
- **HTML5** - Modern markup
- **CSS3** - Styling with animations
- **JavaScript** - Interactive functionality
- **WebRTC** - Browser camera access

## 📊 Features in Detail

### Product Analysis
- Automatic product identification
- Brand recognition
- Category classification
- Barcode scanning (if visible)

### Ingredient Analysis
- Complete ingredient list extraction
- Ingredient categorization
- Natural vs artificial classification
- Processing level assessment

### Health Analysis
- Allergen detection
- Health risk assessment
- Dietary suitability
- Nutritional insights

### Safety Rating
- **GREEN (80-100)**: Safe for consumption
- **YELLOW (60-79)**: Moderate concerns
- **RED (0-59)**: High health concerns

## 📄 Documentation

- [Complete Setup Guide](README_FINAL.md)
- [Environment Variables Guide](ENV_SETUP_GUIDE.md)
- [API Key Setup](API_KEYS_SETUP.md)
- [PDF Download Guide](PDF_DOWNLOAD_GUIDE.md)
- [Gemini AI Configuration](GEMINI_FIXED.md)
- [Project Summary](PROJECT_SUMMARY.md)

## 🧪 Testing

Run the diagnostic test:
```bash
python test_scanner.py
```

Test the scanner endpoint:
```bash
# Open in browser
http://localhost:5000/test/scanner
```

## 🔒 Security

- API keys stored in `.env` file (not committed to Git)
- `.gitignore` configured to protect sensitive data
- Session-based security
- Input validation and sanitization

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for powerful product analysis
- Flask community for excellent web framework
- ReportLab for PDF generation
- OpenCV for image processing

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the documentation in the `docs/` folder
- Review the troubleshooting guides

## 🎯 Roadmap

- [ ] Add database for persistent storage
- [ ] Implement user authentication (optional)
- [ ] Add more AI models for comparison
- [ ] Mobile app support
- [ ] Multi-language support
- [ ] Barcode database integration
- [ ] Nutrition facts extraction
- [ ] Recipe suggestions

## ⚡ Performance

- **Analysis Speed**: 2-5 seconds
- **Accuracy**: Very high with Gemini 2.5 Flash
- **Supported Formats**: JPG, JPEG, PNG
- **Max Image Size**: 10MB

## 🌟 Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Scan Results
![Results](docs/screenshots/results.png)

### PDF Report
![PDF Report](docs/screenshots/pdf-report.png)

---

**Made with ❤️ using Flask and Gemini AI**

*Last Updated: January 7, 2026*
