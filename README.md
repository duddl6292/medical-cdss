# Medical CDSS

BHSD 뇌출혈 CT를 대상으로 nnU-Net 기반 병변 분할 결과를 제공하는 웹 프로젝트입니다.

## Architecture

React → Django REST API → FastAPI Gateway → MOSEC → nnU-Net

## Repository Structure

- `frontend/`: React + Vite
- `backend/`: Django REST API
- `inference/`: MOSEC inference service
- `packages/bhsd_nnunet/`: shared custom nnU-Net code
- `training/`: training and Optuna experiments
- `contracts/`: API contracts
- `deploy/`: Cloud Run deployment configuration
- `.github/`: CI/CD workflows

## Required Versions

- Python 3.12
- Node.js 24
- NumPy 2.0.2
- nnU-Net v2 2.8.1
- Optuna 4.4.0

## Local Ports

- React: 5173
- Django: 8000
- MOSEC: 8001 locally or 8080 on Cloud Run

## Branches

- `main`: final and deployable code
- `dev`: integration branch
- personal branches: individual development

## Security

Do not commit:

- `.env`
- medical images
- model checkpoints
- patient data
- service account keys
