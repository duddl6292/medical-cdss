# FastAPI Inference Gateway

Django와 MOSEC 사이에서 추론 요청을 검증하고 전달하는 API Gateway입니다.

## Architecture

React → Django REST API → FastAPI Gateway → MOSEC → nnU-Net

## Responsibilities

- Django 추론 요청 검증
- MOSEC 요청 형식 변환
- MOSEC timeout 처리
- MOSEC 오류를 표준 HTTP 오류로 변환
- 추론 응답 형식 표준화
- Health Check 제공

## Local setup

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
Copy-Item .env.example .env

uvicorn app.main:app --reload --port 8100