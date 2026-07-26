# BHSD 2.5D Architecture Sweep

## 목적

기존 Exp05 PlainConvUNet의 데이터, fold, optimizer, learning rate, loss 및 effective batch를 유지하고 네트워크 구조만 변경해 비교한다. Test는 구조 선택에 사용하지 않는다.

## 실험

| ID | Trainer | Baseline 대비 변경 |
|---|---|---|
| EXP01_residual_encoder | nnUNetTrainerBHSDResidualEncoderSweep | Plain encoder를 residual basic-block encoder로 변경 |
| EXP02_stage_attention | nnUNetTrainerBHSDStageAttentionSweep | encoder skip stage 3, 4, 5(0-based)에 lightweight attention 추가 |
| EXP03_more_conv_blocks | nnUNetTrainerBHSDMoreConvSweep | encoder/decoder stage당 conv block 2개를 3개로 변경 |
| EXP04_dropout | nnUNetTrainerBHSDDropoutSweep | Dropout2d(p=0.2) 추가 |

검증된 파라미터 수는 각각 Residual 66,966,702개, Stage Attention 46,400,222개, More Conv 64,420,558개, Dropout 46,325,134개다.

SE/CBAM 실험은 요청에 따라 제외했다.

## 공통 조건

- 입력: 인접 3 slice를 channel로 사용하는 2.5D
- 내부 연산: Conv2d
- dataset/fold: Dataset001, fold 0
- physical batch: 1
- gradient accumulation: 12
- effective batch: 12
- optimizer: SGD(momentum=0.99, Nesterov)
- initial LR: 0.009239150319627255
- scheduler: cosine
- loss: Dice+CE
- model selection: 전체 validation 976 case의 raw Micro Dice
- selection threshold: 0.5 고정
- threshold/component-size 탐색: 구조 선택 완료 후 최종 후보에서만 수행
- sweep 종료 시 구조별 NIfTI prediction 재생성은 생략하고 metric만 저장

주의: physical batch 1의 gradient accumulation은 기존 physical batch 12의 batch-Dice와 수학적으로 완전히 같지 않다.

## 실행

```bash
cd /home/stu03/projects/medical-cdss
source .venv/bin/activate
python training/scripts/run_architecture_sweep.py
```

실패로 표시된 실험을 다시 시도하려면:

```bash
python training/scripts/run_architecture_sweep.py --retry-failed
```

동일 명령을 다시 실행하면 완료된 실험은 건너뛰고, `checkpoint_latest.pth`가 있으면 재개한다. latest가 없고 best만 있으면 runner가 best를 latest로 원자적으로 복사한 후 `--c`로 복구한다.

## 안전장치

- 한 GPU에서 순차 실행
- `nnUNet_compile=false`
- `nnUNet_n_proc_DA=0`
- 실험별 결과 폴더 격리
- 5 epoch마다 latest checkpoint
- best checkpoint는 전체 validation Micro Dice 개선 시 저장
- `.tmp` 파일 저장 후 `os.replace`하는 atomic checkpoint/JSON 저장
- 한 실험 실패 시 최대 3회 재시도 후 다음 실험 계속
- 시작 전 최소 8 GiB 여유 공간 확인
- SIGINT/SIGTERM 전달
- manifest 기반 재실행/재개

SIGKILL, 물리 서버 장애 또는 2 GiB RAM 제한으로 인한 OOM을 완전히 방지할 수는 없다. runner는 학습 프로세스가 종료된 뒤 살아 있으면 재시도하며, 컨테이너 전체가 재시작된 경우 같은 명령을 다시 실행하면 manifest와 checkpoint에서 이어간다.

## 저장 형식

```text
/home/stu03/medical-data/architecture_sweep/
├── sweep_manifest.json
├── sweep_summary.csv
├── EXP01_residual_encoder/
│   ├── runner.log
│   ├── epoch_status.jsonl
│   └── Dataset001_BHSD_25D/
│       └── <Trainer>__nnUNetPlans__2d/
│           └── fold_0/
│               ├── architecture.json
│               ├── baseline_diff.json
│               ├── experiment_config.json
│               ├── validation_metrics.json
│               ├── checkpoint_best.pth
│               ├── checkpoint_latest.pth
│               ├── checkpoint_final.pth
│               ├── debug.json
│               ├── progress.png
│               └── training_log_*.txt
├── EXP02_stage_attention/
├── EXP03_more_conv_blocks/
└── EXP04_dropout/
```

`checkpoint_latest.pth`는 정상 완료 시 nnU-Net 정리 과정에서 삭제될 수 있다. 완료 모델은 `checkpoint_best.pth`와 `checkpoint_final.pth`로 보관한다.

## 비교 결과

`sweep_summary.csv`에는 다음 열이 저장된다.

- experiment_id
- trainer
- status
- attempts
- best_epoch
- validation_micro_dice
- last_error
- result_dir

구조 선택은 `validation_micro_dice`가 가장 높은 완료 실험으로 한다. 선택 이후 해당 best checkpoint만 대상으로 validation threshold와 minimum component size를 탐색하고, 고정된 후처리 설정으로 Test를 한 번만 평가한다.
