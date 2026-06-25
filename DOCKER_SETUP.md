# Docker Setup & Guide

You can run the Food Scanner Backend containerized using **Docker** and **Docker Compose**. This ensures that all required system libraries (like `Tesseract OCR`, `ZBar` for barcode decoding, and `OpenCV` graphical libs) are installed automatically, preventing OS-level dependency mismatches.

---

## Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

---

## 1. Running with Docker Compose (Recommended)

Docker Compose loads the `.env` configuration automatically and mounts the source files so the server hot-reloads when you make changes.

### Start the Container
In the project root, run:
```bash
docker-compose up --build -d
```

### Stop the Container
```bash
docker-compose down
```

### View Application Logs
```bash
docker-compose logs -f
```

---

## 2. Running with Standalone Docker

If you prefer building and running standalone images:

### Build the Image
```bash
docker build -t food-scanner-backend .
```

### Run the Container
Pass your `.env` file containing API keys when starting the image:
```bash
docker run -p 5000:5000 --env-file .env --name food_scanner_backend -d food-scanner-backend
```

### Stop the Container
```bash
docker stop food_scanner_backend
docker rm food_scanner_backend
```

---

## Technical Details

The [Dockerfile](file:///c:/food-product-scanner-main/Dockerfile) uses `python:3.10-slim` as its base and installs:
- `libzbar0`: System package required by the `pyzbar` python package to decode EAN/UPC barcodes.
- `tesseract-ocr`: Optical Character Recognition engine needed by `pytesseract` to parse ingredient lists from label images.
- `libgl1-mesa-glx` & `libglib2.0-0`: OpenGL and GLib system libraries needed by `opencv-python (cv2)` to run.
