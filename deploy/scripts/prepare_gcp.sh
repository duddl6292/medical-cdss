#!/usr/bin/env bash
set -euo pipefail

required=(
  PROJECT_ID REGION MODEL_BUCKET DATA_BUCKET
  MOSEC_SERVICE GATEWAY_SERVICE
  MOSEC_SERVICE_ACCOUNT GATEWAY_SERVICE_ACCOUNT
  BACKEND_SERVICE_ACCOUNT MIGRATOR_SERVICE_ACCOUNT
)

for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
done

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com \
  firebase.googleapis.com \
  firebasehosting.googleapis.com \
  --project "${PROJECT_ID}"

create_service_account() {
  local email="$1"
  local account_id="${email%%@*}"
  if ! gcloud iam service-accounts describe "${email}" \
    --project "${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud iam service-accounts create "${account_id}" \
      --project "${PROJECT_ID}" \
      --display-name "${account_id}"
  fi
}

create_service_account "${MOSEC_SERVICE_ACCOUNT}"
create_service_account "${GATEWAY_SERVICE_ACCOUNT}"
create_service_account "${BACKEND_SERVICE_ACCOUNT}"
create_service_account "${MIGRATOR_SERVICE_ACCOUNT}"

if ! gcloud storage buckets describe "gs://${DATA_BUCKET}" \
  --project "${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${DATA_BUCKET}" \
    --project "${PROJECT_ID}" \
    --location "${REGION}" \
    --uniform-bucket-level-access \
    --public-access-prevention
fi

gcloud storage buckets update "gs://${DATA_BUCKET}" \
  --project "${PROJECT_ID}" \
  --lifecycle-file deploy/cloudrun/data-lifecycle.json

for role in roles/storage.objectViewer roles/storage.objectCreator; do
  gcloud storage buckets add-iam-policy-binding "gs://${DATA_BUCKET}" \
    --member "serviceAccount:${MOSEC_SERVICE_ACCOUNT}" \
    --role "${role}"
done

for role in roles/storage.objectViewer roles/storage.objectCreator; do
  gcloud storage buckets add-iam-policy-binding "gs://${DATA_BUCKET}" \
    --member "serviceAccount:${BACKEND_SERVICE_ACCOUNT}" \
    --role "${role}"
done

gcloud storage buckets add-iam-policy-binding "gs://${MODEL_BUCKET}" \
  --member "serviceAccount:${MOSEC_SERVICE_ACCOUNT}" \
  --role roles/storage.objectViewer

for account in "${BACKEND_SERVICE_ACCOUNT}" "${MIGRATOR_SERVICE_ACCOUNT}"; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member "serviceAccount:${account}" \
    --role roles/cloudsql.client
done

gcloud run services add-iam-policy-binding "${MOSEC_SERVICE}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --member "serviceAccount:${GATEWAY_SERVICE_ACCOUNT}" \
  --role roles/run.invoker

# Run this binding after the Gateway service has been created.
if gcloud run services describe "${GATEWAY_SERVICE}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" >/dev/null 2>&1; then
  gcloud run services add-iam-policy-binding "${GATEWAY_SERVICE}" \
    --project "${PROJECT_ID}" \
    --region "${REGION}" \
    --member "serviceAccount:${BACKEND_SERVICE_ACCOUNT}" \
    --role roles/run.invoker
fi
