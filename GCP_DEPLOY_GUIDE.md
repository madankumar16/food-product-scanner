# Deploying Backend to Google Cloud Console (Cloud Run)

This guide walks you through deploying the fully-featured containerized Food Scanner Backend to **Google Cloud Run** using the automated deployment scripts.

Google Cloud Run builds and runs our container directly from the [Dockerfile](file:///c:/food-product-scanner-main/Dockerfile), which means all critical system binary dependencies (like Tesseract OCR and ZBar barcode decoding) are installed and fully operational.

---

## Prerequisites

1. **Google Cloud Account**: Sign up at [Google Cloud Console](https://console.cloud.google.com/).
2. **Billing Enabled**: Make sure billing is enabled for your Google Cloud project (Cloud Run requires a billing account, though it has a generous free tier of 2 million requests/month).
3. **Google Cloud SDK (gcloud CLI)**: Install it on your local machine:
   - [Google Cloud SDK Installation Guide](https://cloud.google.com/sdk/docs/install)
4. **Log in to gcloud**: Run the login command locally:
   ```bash
   gcloud auth login
   ```
5. **Set project ID**: Configure your active project ID:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

---

## Deployment Steps

We have provided automated scripts for both Linux/macOS and Windows hosts in the project root folder.

### On Linux or macOS (Bash)
1. Set executable permissions on the script:
   ```bash
   chmod +x deploy_gcp.sh
   ```
2. Run the deployment script:
   ```bash
   ./deploy_gcp.sh
   ```

### On Windows (Command Prompt)
1. Run the batch script:
   ```cmd
   deploy_gcp.bat
   ```

### What the Scripts Do
1. Enable the Google Cloud Build and Cloud Run API services.
2. Submit your local directory to **Google Cloud Build** which builds the Docker container image in the cloud.
3. Deploy the container image to **Google Cloud Run** in the `us-central1` region, exposing port `5000` and permitting public web access.

---

## Configuring API Keys (Environment Variables)

Once the service is deployed, you must supply your `.env` variables (such as your Gemini API Key) to the Cloud Run instance:

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to **Cloud Run** and click on your service (`food-scanner-backend`).
3. Click **Edit & Deploy New Revision**.
4. Scroll down to the **Variables** tab.
5. Add your environment variables:
   - `GEMINI_API_KEY`: *your-api-key*
6. Click **Deploy** to roll out the update.
