# GCP Runtime Mapping

This document separates verified resource identifiers from values that must be
created or selected at deployment time.

## Verified identifiers

| Resource | Value |
|---|---|
| Project | `stroke-segmentation-123456` |
| Region | `asia-southeast1` |
| Cloud SQL | `medical-cdss-pg17` / PostgreSQL 17 |
| Cloud SQL connection | `stroke-segmentation-123456:asia-southeast1:medical-cdss-pg17` |
| Model bucket | `deep-learning-stroke2607-models-choi` |
| Model object | `nnunet/stroke-bhsd-nnunet-25d-final-model-v1.0.0/STROKE_BHSD_nnUNET_25D_Final_Model_v1.0.0.zip` |
| Model SHA-256 | `9e7ff8a97c2eb21597df4f0ea4f0c6d70a5691e8ee2b17dae755c55edd024a49` |
| Model version | `1.0.0` |

The earlier Cloud Run service `deep-learning-stroke2607` is not silently reused
as the strict v1 MOSEC service. Reuse is safe only after its `/inference`
request and response are verified against `contracts/mosec-api.md`.

## Fixed service flow

```text
React
  -> medical-cdss-backend (Django)
  -> medical-cdss-gateway (FastAPI)
  -> medical-cdss-mosec (MOSEC + nnU-Net, GPU)
  -> Cloud Storage artifacts

Django -> Cloud SQL PostgreSQL 17
```

Django never calls MOSEC directly. MOSEC never writes PostgreSQL.

## Build

Run from the repository root:

```bash
gcloud builds submit \
  --project stroke-segmentation-123456 \
  --region asia-southeast1 \
  --config deploy/cloudbuild/services.yaml \
  --substitutions _REGION=asia-southeast1,_AR_REPOSITORY=bhsd-models
```

Use the created commit tag as `IMAGE_TAG`, load
`deploy/cloudrun/runtime.env.example`, fill the two deployment-specific
placeholders, and run `deploy/scripts/deploy_cloud_run.sh`.

## Required IAM

The runtime service account needs:

- Cloud SQL Client for `medical-cdss-pg17`.
- Storage Object Viewer for the model and uploaded CT objects.
- Storage Object Creator for the inference result prefix.
- Secret Manager Secret Accessor for the two backend secrets.

The deployment script currently enables unauthenticated HTTP access so the
existing React demonstration can call Django and the services can call each
other without an identity-token implementation. Before production or clinical
data use, make Gateway and MOSEC private and add Cloud Run service-to-service
authentication.

## Official references

- Cloud Run GPU:
  https://docs.cloud.google.com/run/docs/configuring/services/gpu
- Cloud Run to Cloud SQL for PostgreSQL:
  https://docs.cloud.google.com/sql/docs/postgres/connect-run
- Cloud Build container images:
  https://docs.cloud.google.com/build/docs/building/build-containers
