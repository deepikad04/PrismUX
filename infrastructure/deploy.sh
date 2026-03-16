#!/usr/bin/env bash
set -euo pipefail

# PrismUX GCP Deployment Script
# Usage: ./deploy.sh [project-id] [region]

PROJECT_ID="${1:-$(gcloud config get-value project)}"
REGION="${2:-us-central1}"
BACKEND_IMAGE="gcr.io/${PROJECT_ID}/prismux-backend"
FRONTEND_IMAGE="gcr.io/${PROJECT_ID}/prismux-frontend"
GCS_BUCKET="${PROJECT_ID}-prismux-screenshots"

echo "=== PrismUX Deployment ==="
echo "Project: ${PROJECT_ID}"
echo "Region:  ${REGION}"
echo ""

# Enable required APIs
echo "--- Enabling APIs ---"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com \
  --project="${PROJECT_ID}"

# Create Firestore database (if not exists)
echo "--- Setting up Firestore ---"
gcloud firestore databases create \
  --location="${REGION}" \
  --project="${PROJECT_ID}" 2>/dev/null || echo "Firestore database already exists"

# Create GCS bucket (if not exists)
echo "--- Setting up Cloud Storage ---"
gcloud storage buckets create "gs://${GCS_BUCKET}" \
  --location="${REGION}" \
  --project="${PROJECT_ID}" 2>/dev/null || echo "Bucket already exists"

# Build and push backend
echo "--- Building Backend ---"
gcloud builds submit ../backend \
  --tag="${BACKEND_IMAGE}" \
  --project="${PROJECT_ID}"

# Build and push frontend
echo "--- Building Frontend ---"
gcloud builds submit ../frontend \
  --tag="${FRONTEND_IMAGE}" \
  --project="${PROJECT_ID}"

# Deploy backend to Cloud Run
echo "--- Deploying Backend ---"
gcloud run deploy prismux-backend \
  --image="${BACKEND_IMAGE}" \
  --platform=managed \
  --region="${REGION}" \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --concurrency=1 \
  --min-instances=0 \
  --max-instances=5 \
  --port=8000 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},GCS_BUCKET_NAME=${GCS_BUCKET},BROWSER_HEADLESS=true,CORS_ORIGINS=*" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
  --project="${PROJECT_ID}"

BACKEND_URL=$(gcloud run services describe prismux-backend \
  --platform=managed --region="${REGION}" --project="${PROJECT_ID}" \
  --format='value(status.url)')
echo "Backend URL: ${BACKEND_URL}"

# Deploy frontend to Cloud Run
echo "--- Deploying Frontend ---"
gcloud run deploy prismux-frontend \
  --image="${FRONTEND_IMAGE}" \
  --platform=managed \
  --region="${REGION}" \
  --memory=256Mi \
  --cpu=1 \
  --port=80 \
  --allow-unauthenticated \
  --set-env-vars="BACKEND_URL=${BACKEND_URL}" \
  --project="${PROJECT_ID}"

FRONTEND_URL=$(gcloud run services describe prismux-frontend \
  --platform=managed --region="${REGION}" --project="${PROJECT_ID}" \
  --format='value(status.url)')

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: ${FRONTEND_URL}"
echo "Backend:  ${BACKEND_URL}"
echo "API Docs: ${BACKEND_URL}/docs"
