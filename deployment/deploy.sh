#!/bin/bash
PROJECT_ID=""
REGION=""
SERVICE_NAME="scraper-service"

PORT=8080
IMAGE_NAME="yogonet-scrapper-app"

gcloud auth login
gcloud config set project $PROJECT_ID
gcloud config list --format="value(core.project)"

echo "Habilitando la API de Google Container Registry y Cloud Run..."
gcloud services enable containerregistry.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable run.googleapis.com

echo "Construyendo la imagen y subiéndola a Google Container Registry..."
gcloud auth configure-docker
docker tag $IMAGE_NAME gcr.io/$PROJECT_ID/$IMAGE_NAME
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME

echo "Desplegando en Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --port $PORT

echo "Despliegue completado. Servicio disponible en la URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
