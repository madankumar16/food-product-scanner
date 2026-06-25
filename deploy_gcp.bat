@echo off
echo ==========================================================
echo Google Cloud Run Deployment Script (Windows)
echo ==========================================================

rem Check if gcloud is installed
where gcloud >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: gcloud CLI is not installed or not in PATH. Please install Google Cloud SDK.
    pause
    exit /b 1
)

set SERVICE_NAME=food-scanner-backend
set REGION=us-central1

rem Get active project ID
for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT_ID=%%i

if "%PROJECT_ID%"=="" (
    echo ERROR: No Google Cloud Project ID is configured in gcloud.
    set /p PROJECT_ID="Please enter your GCP Project ID: "
)

if "%PROJECT_ID%"=="(unset)" (
    echo ERROR: No Google Cloud Project ID is configured in gcloud.
    set /p PROJECT_ID="Please enter your GCP Project ID: "
)

if "%PROJECT_ID%"=="" (
    echo Project ID is required. Exiting.
    pause
    exit /b 1
)

gcloud config set project %PROJECT_ID%

echo Using GCP Project: %PROJECT_ID%
echo Service Name:      %SERVICE_NAME%
echo Deployment Region: %REGION%
echo ----------------------------------------------------------
set /p PROCEED="Proceed with deployment? (y/n): "

if /i "%PROCEED%" neq "y" (
    echo Deployment cancelled.
    exit /b 0
)

echo Enabling Google Cloud Build and Cloud Run APIs...
gcloud services enable run.googleapis.com builds.googleapis.com

echo Submitting build to Google Cloud Build...
gcloud builds submit --tag gcr.io/%PROJECT_ID%/%SERVICE_NAME%

echo Deploying container to Google Cloud Run...
gcloud run deploy %SERVICE_NAME% --image gcr.io/%PROJECT_ID%/%SERVICE_NAME% --platform managed --region %REGION% --allow-unauthenticated --port 5000

echo ==========================================================
echo SUCCESS: Food Scanner Backend deployed to Google Cloud Run!
gcloud run services describe %SERVICE_NAME% --platform managed --region %REGION% --format "value(status.url)"
echo ==========================================================
pause
