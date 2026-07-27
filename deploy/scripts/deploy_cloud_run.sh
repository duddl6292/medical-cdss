#!/usr/bin/env bash
set -euo pipefail

required=(
  PROJECT_ID REGION AR_REPOSITORY
  MOSEC_SERVICE GATEWAY_SERVICE BACKEND_SERVICE
  CLOUD_SQL_CONNECTION DB_NAME DB_APP_USER DB_MIGRATOR_USER
  DB_APP_PASSWORD_SECRET DB_MIGRATOR_PASSWORD_SECRET
  DJANGO_SECRET_KEY_SECRET MODEL_BUCKET DATA_BUCKET MODEL_OBJECT MODEL_SHA256
  RESULTS_URI_PREFIX MODEL_VERSION
  MOSEC_SERVICE_ACCOUNT GATEWAY_SERVICE_ACCOUNT
  BACKEND_SERVICE_ACCOUNT MIGRATOR_SERVICE_ACCOUNT FRONTEND_ORIGIN
)

for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
done

tag="${IMAGE_TAG:-manual}"
image_root="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPOSITORY}"
mosec_image="${image_root}/medical-cdss-mosec:${tag}"
gateway_image="${image_root}/medical-cdss-gateway:${tag}"
backend_image="${image_root}/medical-cdss-backend:${tag}"

gcloud run deploy "${MOSEC_SERVICE}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --image "${mosec_image}" \
  --service-account "${MOSEC_SERVICE_ACCOUNT}" \
  --cpu 4 \
  --memory 16Gi \
  --no-cpu-throttling \
  --gpu 1 \
  --gpu-type nvidia-l4 \
  --no-gpu-zonal-redundancy \
  --concurrency 1 \
  --timeout 900 \
  --max-instances 1 \
  --set-env-vars "MODEL_BUCKET=${MODEL_BUCKET},MODEL_OBJECT=${MODEL_OBJECT},MODEL_SHA256=${MODEL_SHA256},MODEL_ID=stroke-bhsd-nnunet-25d-final-model,MODEL_VERSION=${MODEL_VERSION},MODEL_FOLDS=0,MODEL_CHECKPOINT=checkpoint_best.pth,MODEL_DEVICE=cuda,RESULTS_URI_PREFIX=${RESULTS_URI_PREFIX},MODEL_CACHE_DIR=/models,MODEL_LOAD_ON_STARTUP=true" \
  --no-allow-unauthenticated

mosec_url="$(
  gcloud run services describe "${MOSEC_SERVICE}" \
    --project "${PROJECT_ID}" \
    --region "${REGION}" \
    --format='value(status.url)'
)"

gcloud run deploy "${GATEWAY_SERVICE}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --image "${gateway_image}" \
  --service-account "${GATEWAY_SERVICE_ACCOUNT}" \
  --cpu 1 \
  --memory 1Gi \
  --timeout 900 \
  --set-env-vars "MOSEC_URL=${mosec_url},MOSEC_AUDIENCE=${mosec_url},MOSEC_TIMEOUT_SECONDS=900" \
  --no-allow-unauthenticated

gateway_url="$(
  gcloud run services describe "${GATEWAY_SERVICE}" \
    --project "${PROJECT_ID}" \
    --region "${REGION}" \
    --format='value(status.url)'
)"

gcloud run deploy "${BACKEND_SERVICE}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --image "${backend_image}" \
  --service-account "${BACKEND_SERVICE_ACCOUNT}" \
  --cpu 2 \
  --memory 2Gi \
  --timeout 900 \
  --add-cloudsql-instances "${CLOUD_SQL_CONNECTION}" \
  --set-env-vars "DJANGO_DEBUG=false,DJANGO_ALLOWED_HOSTS=*,CORS_ALLOWED_ORIGINS=${FRONTEND_ORIGIN},CSRF_TRUSTED_ORIGINS=${FRONTEND_ORIGIN},DB_NAME=${DB_NAME},DB_USER=${DB_APP_USER},DB_SCHEMA=medical_cdss,DB_HOST=/cloudsql/${CLOUD_SQL_CONNECTION},DB_PORT=5432,DB_CONN_MAX_AGE=60,GS_BUCKET_NAME=${DATA_BUCKET},INFERENCE_GATEWAY_URL=${gateway_url}/api/v1/inference,INFERENCE_GATEWAY_AUDIENCE=${gateway_url},INFERENCE_TIMEOUT_SECONDS=900,MODEL_VERSION=${MODEL_VERSION},MAX_NIFTI_UPLOAD_BYTES=536870912" \
  --set-secrets "DB_PASSWORD=${DB_APP_PASSWORD_SECRET}:latest,DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY_SECRET}:latest" \
  --allow-unauthenticated

gcloud run jobs deploy "${BACKEND_SERVICE}-migrate" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --image "${backend_image}" \
  --service-account "${MIGRATOR_SERVICE_ACCOUNT}" \
  --set-cloudsql-instances "${CLOUD_SQL_CONNECTION}" \
  --set-env-vars "DJANGO_DEBUG=false,DB_NAME=${DB_NAME},DB_USER=${DB_MIGRATOR_USER},DB_APP_USER=${DB_APP_USER},DB_SCHEMA=medical_cdss,DB_HOST=/cloudsql/${CLOUD_SQL_CONNECTION},DB_PORT=5432,DB_CONN_MAX_AGE=0" \
  --set-secrets "DB_PASSWORD=${DB_MIGRATOR_PASSWORD_SECRET}:latest,DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY_SECRET}:latest" \
  --command python \
  --args manage.py,migrate_poc \
  --max-retries 0 \
  --task-timeout 10m
