# Model Artifacts

실제 모델 체크포인트는 Git 저장소에 커밋하지 않는다.

모델은 Google Cloud Storage 또는 별도 공유 저장소에서 관리한다.

필요한 파일 예시:

- checkpoint_best.pth
- dataset.json
- plans.json
- fold_0/
- model_manifest.json
