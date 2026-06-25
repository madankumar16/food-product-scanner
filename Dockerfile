# Use an official lightweight Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for OpenCV, pyzbar, and Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libzbar0 \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for caching optimization
COPY requirements.txt /app/

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose port 5000 for the Flask server
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
