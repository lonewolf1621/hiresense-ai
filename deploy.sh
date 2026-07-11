#!/bin/bash

echo "🚀 HireSense AI - GCP Deployment Script"
echo "========================================"

# Set GCP Project
PROJECT_ID="hiresense-ai-prod"
REGION="asia-south1"
SERVICE_NAME="hiresense-api"

echo "Setting GCP Project..."
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

echo "Authenticating with GCP..."
gcloud auth login

echo "Creating Artifact Registry Repository..."
gcloud artifacts repositories create hiresense-repo \
  --repository-format=docker \
  --location=$REGION || echo "Repository already exists"

echo "Building and Pushing Docker Image..."
gcloud builds submit \
  --tag $REGION-docker.pkg.dev/$PROJECT_ID/hiresense-repo/$SERVICE_NAME:latest

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/hiresense-repo/$SERVICE_NAME:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 3600 \
  --max-instances 100 \
  --set-env-vars "SECRET_KEY=your-secret-key,GCP_PROJECT_ID=$PROJECT_ID,GCS_BUCKET_NAME=hiresense-ai-resumes"

echo "✅ Deployment complete!"
echo "Your API is live at the URL shown above"