# Food Product Scanner Mobile App (Flutter)

A cross-platform Flutter mobile application designed to scan food product barcodes, pull analyses from our local python Flask backend, and display detailed health metrics, allergens, safety scores, and Gemini AI expert summaries.

## Key Features
- **Real-Time Scanning**: Integrated camera-based scanning via `mobile_scanner`.
- **Lookup Query**: Text search for barcodes manually.
- **Offline Scans & Favorites**: Save scans locally on the device using `shared_preferences` for offline viewing, with support for flagging Favorites.
- **Visual Nutri-Score**: Customized badge showing official FSA-NPS category-aware ratings.
- **AI insights**: Displays ingredient risk levels and AI summaries.

## Getting Started

### 1. Prerequisites
- [Flutter SDK](https://docs.flutter.dev/get-started/install) installed and configured on your machine.
- An emulator or physical Android/iOS device connected.

### 2. Configure Backend API URL
The app communicates with the Flask server. By default, it connects to:
- Android Emulator default address: `http://10.0.2.2:5000`

If you are running the app on a physical device or iOS Simulator, update the backend URL inside `lib/services/api_service.dart`:
- iOS Simulator: Use `http://localhost:5000`
- Physical Device: Use `http://<your-computer-ip-address>:5000`

### 3. Install Dependencies
Navigate to the mobile app directory and fetch dependencies:
```bash
cd food_scanner_mobile
flutter pub get
```

### 4. Run the Backend Server
Make sure your Flask server is running in another terminal window:
```bash
python app.py
```

### 5. Launch the Mobile App
Build and run the app on your selected emulator or device:
```bash
flutter run
```

## Testing on Emulators
Because emulators lack physical food boxes/labels to scan:
1. Open the **Scan** tab.
2. Tap on any of the **Quick Simulators** buttons (Nutella, Coca-Cola, Oreo) to instantly simulate scanning a product and load its results from the live backend database!
3. Alternatively, enter a manual barcode in the text field (e.g. `3017620425035`) and press the arrow button.
