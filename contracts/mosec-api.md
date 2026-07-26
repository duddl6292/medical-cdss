# MOSEC Inference API Contract v1

## 1. Scope

This document fixes the JSON contract used by:

```text
Django REST API → FastAPI Gateway → MOSEC → nnU-Net Exp05 2.5D
```

- Gateway endpoint: `POST /api/v1/inference`
- Internal MOSEC endpoint: `POST /inference`
- Content type: `application/json`
- Schema version: `1.0`
- Processing mode: synchronous between Gateway and MOSEC

MOSEC uses JSON by default. `Worker.forward()` therefore receives one decoded
JSON object when dynamic batching is disabled (`max_batch_size=1`) and returns
one JSON object.

## 2. Fixed model behavior

The deployed model is the final BHSD nnU-Net Exp05 3-slice 2.5D model.

- Trainer: `nnUNetTrainerBHSD_Exp05_25DFinal`
- Architecture: `PlainConvUNet`
- NIfTI slice axis: `2`
- nnU-Net configuration: `2d`
- 2.5D channels: center-1, center, center+1
- Boundary policy: edge replication
- Segmentation decision: nnU-Net default label conversion
- Output label: `0=background`, `1=hemorrhage`

`threshold` and `min_component_size` are not request fields in v1. The current
validated Exp05 pipeline does not use them. An option must not be exposed by
the API until the model pipeline actually implements and validates it.

The architecture-sweep trainers added in dev commit `e46e2f0` are training
candidates, not deployed-model replacements. Their Test inference was not
complete when the commit was merged. Changing the deployed trainer or
architecture therefore requires a separately approved model version.

## 3. Request

```json
{
  "schema_version": "1.0",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "case_id": 1,
  "input_uri": "gs://medical-cdss/uploads/1/image.nii.gz",
  "model_version": "1.0.0"
}
```

| Field | Type | Required | Rule |
|---|---|---:|---|
| `schema_version` | string | Yes | Must be `"1.0"` |
| `job_id` | UUID string | Yes | Correlation ID created by Django |
| `case_id` | positive integer | Yes | Must equal Django `Case.ct_id` |
| `input_uri` | string | Yes | Must be a `gs://.../*.nii.gz` object URI |
| `model_version` | string | Yes | Must match the model loaded by MOSEC |

Unknown fields are rejected. The request does not contain CT bytes, a local
filesystem path, patient name, resident number, or other direct identifier.

## 4. Completed response

```json
{
  "schema_version": "1.0",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "case_id": 1,
  "status": "completed",
  "model_version": "1.0.0",
  "input": {
    "shape": [512, 512, 32],
    "spacing_mm": [0.488281, 0.488281, 5.093584]
  },
  "model": {
    "model_id": "stroke-bhsd-nnunet-25d-final-model",
    "model_version": "1.0.0",
    "trainer_name": "nnUNetTrainerBHSD_Exp05_25DFinal",
    "architecture": "PlainConvUNet",
    "folds": [0],
    "checkpoint": "checkpoint_best.pth",
    "nnunet_configuration": "2d",
    "input_mode": "2.5D_3Slice",
    "slice_axis": 2,
    "context_offsets": [-1, 0, 1],
    "boundary_policy": "edge_replication",
    "target_policy": "center_slice_mask",
    "segmentation_decision": "nnunet_default_label_conversion"
  },
  "artifacts": {
    "mask_uri": "gs://medical-cdss/results/550e8400-e29b-41d4-a716-446655440000/mask.nii.gz",
    "result_json_uri": "gs://medical-cdss/results/550e8400-e29b-41d4-a716-446655440000/result.json",
    "preview_uri": null,
    "probability_uri": null,
    "entropy_uri": null,
    "uncertainty_uri": null
  },
  "result": {
    "lesion_detected": true,
    "lesion_voxel_count": 56520,
    "voxel_volume_mm3": 1.2144038162639903,
    "lesion_volume_mm3": 68638.10369524073,
    "lesion_volume_ml": 68.63810369524073,
    "lesion_slice_count": 3,
    "lesion_slice_indices": [14, 15, 16],
    "lesion_slice_start": 14,
    "lesion_slice_end": 16,
    "max_lesion_slice": 15,
    "max_lesion_slice_voxel_count": 24810,
    "slice_axis": 2,
    "slice_index_base": 0
  },
  "performance": {
    "input_download_seconds": 0.8,
    "context_preparation_seconds": 1.2,
    "inference_seconds": 13.7,
    "postprocessing_seconds": 0.8,
    "output_upload_seconds": 0.6,
    "total_seconds": 17.1,
    "gpu_memory_measured": true,
    "gpu_peak_memory_mb": 8421.5
  },
  "summary": "AI가 출혈 의심 영역을 3개 슬라이스에서 분할했으며, 계산된 병변 부피는 68.64 mL입니다.",
  "message": "AI 분석 결과이며 의료진의 최종 진단을 대체하지 않습니다.",
  "error": null
}
```

### Completed-response rules

- `status` must be `"completed"`.
- `input`, `model`, `artifacts`, `result`, `performance`, `summary`, and
  `message` must be present.
- `error` must be `null`.
- `model_version` must equal `model.model_version`.
- `trainer_name` and `architecture` identify the exact code required to load
  the checkpoint. For model version `1.0.0` they are
  `nnUNetTrainerBHSD_Exp05_25DFinal` and `PlainConvUNet`.
- `folds` contains non-negative integers, or the single value `"all"`.
- Slice indices are zero-based and use NIfTI array axis `2`.
- When no lesion is detected, voxel/volume/slice counts are zero, the slice
  index list is empty, and start/end/max slice fields are `null`.
- Probability, entropy, uncertainty, and preview URIs remain `null` until
  their generation and upload are implemented and validated.

## 5. Failed response

```json
{
  "schema_version": "1.0",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "case_id": 1,
  "status": "failed",
  "model_version": "1.0.0",
  "input": null,
  "model": null,
  "artifacts": null,
  "result": null,
  "performance": null,
  "summary": null,
  "message": null,
  "error": {
    "code": "INVALID_NIFTI_DIMENSION",
    "message": "The input NIfTI volume must be three-dimensional.",
    "retryable": false
  }
}
```

### Failed-response rules

- `status` must be `"failed"`.
- `error` is required.
- All success-only fields must be `null`.
- `error.code` is a stable uppercase machine-readable code.
- `error.message` is safe for logs and must not expose credentials, signed
  URLs, patient data, or local filesystem paths.
- `error.retryable` tells Django whether retrying the same job can be useful.

## 6. Status ownership

The synchronous MOSEC endpoint returns only:

- `completed`
- `failed`

`waiting` and `processing` belong to Django's persisted job lifecycle and are
not MOSEC response values.

| Django status | Meaning |
|---|---|
| `waiting` | Job created but Gateway call has not started |
| `processing` | Gateway/MOSEC inference is running |
| `completed` | MOSEC completed and Django saved the result |
| `failed` | Gateway/MOSEC failed and Django saved the error |

## 7. HTTP handling

- Schema validation error: MOSEC request failure, mapped by Gateway to a 4xx
  contract error.
- MOSEC connection, timeout, or invalid JSON error: Gateway returns `502`.
- MOSEC completed/failed JSON: Gateway validates this v1 response before
  returning it to Django.

The `job_id` and `case_id` in the response must exactly match the request.

## 8. Versioning

The v1 field names and meanings must not change silently.

- Compatible optional addition: update this document and examples.
- Required-field removal, rename, type change, or meaning change: create a new
  contract and endpoint such as `/api/v2/inference`.
