#!/bin/bash

# Exit on error
set -e

echo "=========================================================="
echo "Google Cloud Run Deployment Script"
echo "=========================================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Load variables
SERVICE_NAME="food-scanner-backend"
REGION="us-central1"

# Get active project ID from gcloud
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    echo "ERROR: No Google Cloud Project ID is configured in gcloud CLI."
    read -p "Please enter your GCP Project ID: " PROJECT_ID
    if [ -z "$PROJECT_ID" ]; then
        echo "Project ID is required. Exiting."
        exit 1
    fi
    gcloud config set project "$PROJECT_ID"
fi

echo "Using GCP Project: $PROJECT_ID"
echo "Service Name:      $SERVICE_NAME"
echo "Deployment Region: $REGION"
echo "----------------------------------------------------------"
read -p "Proceed with deployment? (y/n): " PROCEED

if [ "$PROCEED" != "y" ] && [ "$PROCEED" != "Y" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# 1. Enable required APIs
echo "Enabling Google Cloud Build and Cloud Run APIs..."
gcloud services enable run.googleapis.com builds.googleapis.com

# 2. Build the Docker image in GCP Cloud Build
echo "Submitting build to Google Cloud Build..."
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME"

# 3. Deploy to Google Cloud Run
echo "Deploying container to Google Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080

# Get Service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform managed --region "$REGION" --format 'value(status.url)')

echo "=========================================================="
echo "SUCCESS: Food Scanner Backend deployed to Google Cloud Run!"
echo "Service URL: $SERVICE_URL"
echo "=========================================================="
