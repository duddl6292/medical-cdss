# medical-cdss 통합 보고서

작성 기준일: 2026-07-27 (Asia/Seoul)

## 1. 비교 기준

| 구분 | 기준 |
|---|---|
| 업로드 백업 ZIP | `c0e56f4` 기반 `yr` 작업본과 미커밋 추론 계약 파일 |
| 최신 직전 `yr` | `2d9ab229c4e357383a8c11e358f97c2396b63e45` |
| 최신 `yr` | `f6f510c541bdc2665b7f0c9de2f4683114c86ec9` |

백업 ZIP의 추론 계약 미커밋 파일은 이후 최신 `yr` 이력에 반영되어
있었다. 따라서 통합본은 최신 `yr`을 기준으로 삼고, ZIP의 오래된
프론트엔드와 설정으로 최신 팀 코드를 되돌리지 않았다.

최신 직전 커밋에서 최신 커밋으로 추가된 핵심은 다음과 같다.

- Cloud Storage 모델 ZIP 다운로드와 SHA-256 검증
- 안전한 모델 압축 해제와 모델 캐시 준비
- Cloud Storage 입력 다운로드와 결과 업로드
- MOSEC 컨테이너 시작 시 모델 준비
- 로컬 ADC 자격 증명 마운트

## 2. 이번 통합에서 수정한 사항

### 2번 담당 범위

- FastAPI Gateway가 MOSEC HTTP 422를 502로 왜곡하던 문제 수정
- `MOSEC_REQUEST_REJECTED`, HTTP 422, `retryable=false`로 계약 통일
- 검증된 Exp05 모델 버킷·객체·SHA-256을 환경 예시에 반영
- `RESULTS_URI_PREFIX`, 모델 캐시와 요청 임시 경로 추가
- Django 8000과 충돌하던 MOSEC 로컬 포트를 호스트 8001로 복구
- Gateway 계약 회귀 테스트 추가

### 3번 담당 경계의 최소 통합

- React 업로드 URL과 Django URL을 `/api/v1/cases/`로 일치
- Django가 MOSEC가 아니라 FastAPI Gateway만 호출하도록 설정명 변경
- `POST /api/v1/cases/{case_id}/predictions/` 구현
- `waiting -> processing -> completed/failed` 상태를 PostgreSQL에 저장
- Gateway의 모델·병변·성능·아티팩트 응답을 `PredictionResult`에 저장
- 오류 코드와 오류 메시지를 `Prediction`에 저장
- 마이그레이션 `0004_gateway_result_fields.py` 추가
- React의 UUID `job_id` 타입과 Django 응답 필드 통일
- 업로드 페이지와 진행 페이지를 실제 Django API에 연결

### GCP 런타임

- PostgreSQL 17 Cloud SQL Unix socket 설정 지원
- Cloud Storage를 Django 기본 업로드 저장소로 선택 가능
- Django Cloud Run용 Gunicorn Dockerfile 추가
- MOSEC·Gateway·Django 3개 이미지 Cloud Build 파일 추가
- Cloud Run 배포 스크립트와 비밀값 분리 템플릿 추가

## 3. 검증된 GCP 식별자

| 항목 | 값 |
|---|---|
| Project | `stroke-segmentation-123456` |
| Region | `asia-southeast1` |
| Cloud SQL | `medical-cdss-pg17` / PostgreSQL 17 |
| Connection name | `stroke-segmentation-123456:asia-southeast1:medical-cdss-pg17` |
| Model bucket | `deep-learning-stroke2607-models-choi` |
| Model object | `nnunet/stroke-bhsd-nnunet-25d-final-model-v1.0.0/STROKE_BHSD_nnUNET_25D_Final_Model_v1.0.0.zip` |
| SHA-256 | `9e7ff8a97c2eb21597df4f0ea4f0c6d70a5691e8ee2b17dae755c55edd024a49` |
| Model version | `1.0.0` |

기존 Cloud Run 서비스 `deep-learning-stroke2607`은 strict v1
`/inference` 계약 검증 없이 새 MOSEC 서비스로 간주하지 않았다.
통합본에서는 역할이 분명한 `medical-cdss-mosec`,
`medical-cdss-gateway`, `medical-cdss-backend`를 사용한다.

## 4. 수행한 검증

- ZIP 압축 무결성 검사: 통과
- ZIP 경로 탈출 검사: 통과
- Python `compileall`: 통과
- `git diff --check`: 통과
- FastAPI Gateway 테스트: 17 passed
- Django API·Gateway 저장 테스트: 2 passed
- Django `manage.py check`: 통과
- Django `makemigrations --check --dry-run`: 변경 없음
- React TypeScript 및 Vite production build: 통과
- Cloud Run 배포 스크립트 `bash -n`: 통과

## 5. 실제 클라우드에서 별도로 확인할 사항

다음 항목은 코드를 실행하지 않고 성공했다고 말할 수 없는 운영 검증이다.

1. 런타임 서비스 계정의 Storage Object Viewer/Creator 권한
2. Cloud SQL Client와 Secret Manager Secret Accessor 권한
3. Cloud Run GPU L4 할당량과 MOSEC 콜드 스타트
4. Cloud SQL 기존 데이터 이관과 실제 `migrate`
5. 모델 ZIP 다운로드·SHA 검증·nnU-Net 체크포인트 로딩
6. 실제 NIfTI 한 건의 end-to-end 추론
7. 비공개 버킷의 `gs://` 마스크를 NiiVue가 읽을 전달 방식

현재 결과 화면과 이력 화면에는 팀원이 만든 시연용 데이터가 일부
남아 있다. 업로드와 진행 화면은 실제 API에 연결했지만, NiiVue가
비공개 Cloud Storage 결과를 표시하려면 Django 프록시 또는 만료
시간이 짧은 서명 URL 정책을 추가로 확정해야 한다.

또한 배포 스크립트는 기존 시연 흐름과의 호환을 위해 HTTP 서비스를
공개로 만든다. 환자 데이터 또는 운영 환경에서는 Gateway와 MOSEC를
비공개로 전환하고 Cloud Run 서비스 간 ID 토큰 인증을 추가해야 한다.

## 6. 로컬에서 적용할 때

이 통합 ZIP은 `.git`, `.env`, 가상환경, 캐시, `node_modules`, 빌드
산출물을 포함하지 않는다. 기존 로컬 저장소에 그대로 덮어쓰기보다
별도 폴더에서 검증한 뒤 필요한 브랜치에 커밋하는 것을 권장한다.
