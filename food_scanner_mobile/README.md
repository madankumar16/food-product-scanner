# Scan Before Use: mobile app (Flutter)

Scan any barcode or QR code with your phone camera and see what it is. The app sends the scanned text to the Scan Before Use server (https://fopack-scanner.vercel.app), which:

- looks up food, cosmetics, pet food and household products in the Open Food Facts family of databases, and books in Open Library
- reads GS1 codes on medicines and fresh food (expiry date, batch, serial) and warns when a product has expired
- decodes everything else from the code itself: links, UPI payment requests, Wi-Fi, contacts, email, phone, SMS, locations, events, plain text

Nothing is made up: if a product isn't in any database, the app says so.

## Features
- **Every format**: QR, Data Matrix, PDF417, Aztec, EAN/UPC, Code 128/39/93, ITF, Codabar, GS1 DataBar (via `mobile_scanner`)
- **Type it**: enter a barcode number, ISBN or any text
- **History and saved items**, stored only on the phone (`shared_preferences`)
- **Food details**: veg status, allergens, Nutri-Score, ingredients; your diet and allergen alerts on the Profile tab

## Get the app
Every push to GitHub builds an Android APK. Open the repository's **Actions** tab, pick the latest **CI** run and download **scan-before-use-apk**. Unzip it and install `app-release.apk` on your phone. You need to allow installing apps from your browser or file manager.

## Build it yourself
The repository holds only the Dart code. Generate the platform folders once, then run:
```bash
cd food_scanner_mobile
flutter create --platforms=android,ios .
flutter pub get
flutter run
```
For Android release builds, add `<uses-permission android:name="android.permission.INTERNET"/>` to `android/app/src/main/AndroidManifest.xml`. For iOS, add an `NSCameraUsageDescription` to `ios/Runner/Info.plist`.

## Testing on Emulators
Emulators have no real packs to scan, so use the text box on the **Scan** tab or the **Lookup** tab:
- `8901058000290` (food), `5010394133852` (pet food), `9780140449136` (book)
- any text or link, e.g. `https://example.com`

By default the app uses the live site. To use a local server instead:
```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:5000
```
