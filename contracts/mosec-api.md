# Inference API Contract v1

## Architecture

Django REST API → FastAPI Gateway → MOSEC → nnU-Net

## External inference endpoint

- Method: `POST`
- Path: `/api/v1/inference`
- Content-Type: `application/json`

## Internal MOSEC endpoint

- Method: `POST`
- Path: `/inference`
- Content-Type: `application/json`

## Request

```json
{
  "job_id": "job-001",
  "case_id": "case-001",
  "input_uri": "gs://medical-cdss/uploads/case-001/image.nii.gz",
  "model_version": "bhsd-nnunet-v1.0.0",
  "parameters": {
    "threshold": 0.25,
    "min_component_size": 30
  }
}
```

## Success response

```json
{
  "job_id": "job-001",
  "case_id": "case-001",
  "status": "completed",
  "model_version": "bhsd-nnunet-v1.0.0",
  "prediction": {
    "mask_uri": null,
    "preview_uri": null,
    "lesion_voxels": 0,
    "lesion_volume_ml": 0.0,
    "shape": [512, 512, 32],
    "spacing": [0.488281, 0.488281, 5.093584],
    "preview_slice_index": 16
  },
  "timing": {
    "preprocessing_seconds": 0.0,
    "inference_seconds": 0.0,
    "postprocessing_seconds": 0.0,
    "total_seconds": 0.0
  },
  "error": null
}
```

## Status values

- `queued`
- `running`
- `completed`
- `failed`

## Versioning rule

The v1 field names and response structure must not be changed without team agreement.

Breaking changes require a new endpoint such as `/api/v2/inference`.