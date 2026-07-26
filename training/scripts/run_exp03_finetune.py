#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/home/stu03/medical-data/architecture_sweep/EXP03_more_conv_blocks/Dataset001_BHSD_25D/nnUNetTrainerBHSDMoreConvSweep__nnUNetPlans__2d/fold_0/checkpoint_best.pth")
OUTPUT_ROOT = Path("/home/stu03/medical-data/architecture_sweep/EXP03_more_conv_blocks_finetune")
TRAINER = "nnUNetTrainerBHSDMoreConvFineTune"
MODEL_DIR = OUTPUT_ROOT / "Dataset001_BHSD_25D" / f"{TRAINER}__nnUNetPlans__2d" / "fold_0"
CONFIG = PROJECT_ROOT / "training/configs/exp03_more_conv_finetune.json"
TRAINER_DIR = PROJECT_ROOT / "packages/bhsd_nnunet/src/bhsd_nnunet/trainers"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_json(path, payload):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


def main():
    if not SOURCE.is_file() or SOURCE.stat().st_size == 0:
        raise FileNotFoundError(f"EXP03 best checkpoint is missing: {SOURCE}")
    if not CONFIG.is_file():
        raise FileNotFoundError(CONFIG)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(OUTPUT_ROOT).free < 8 * 1024**3:
        raise RuntimeError("Fine-tuning requires at least 8 GiB free disk space.")

    final = MODEL_DIR / "checkpoint_final.pth"
    if final.is_file():
        print(f"Already completed; leaving results unchanged: {final}")
        return 0

    latest = MODEL_DIR / "checkpoint_latest.pth"
    resume = latest.is_file() and latest.stat().st_size > 0
    command = [str(PROJECT_ROOT / ".venv/bin/nnUNetv2_train"), "1", "2d", "0", "-tr", TRAINER, "-p", "nnUNetPlans", "-device", "cuda"]
    if resume:
        command.append("--c")

    env = os.environ.copy()
    env.update({
        "nnUNet_raw": "/home/stu03/medical-data/nnUNet_raw",
        "nnUNet_preprocessed": "/home/stu03/medical-data/nnUNet_preprocessed",
        "nnUNet_results": str(OUTPUT_ROOT),
        "nnUNet_extTrainer": str(TRAINER_DIR),
        "BHSD_CONFIG_PATH": str(CONFIG),
        "BHSD_FINETUNE_CHECKPOINT": str(SOURCE),
        "BHSD_STATUS_PATH": str(OUTPUT_ROOT / "epoch_status.jsonl"),
        "nnUNet_compile": "false",
        "nnUNet_n_proc_DA": "0",
        "PYTHONUNBUFFERED": "1",
    })
    atomic_json(OUTPUT_ROOT / "finetune_lineage.json", {
        "created_at": now(),
        "source_checkpoint": str(SOURCE),
        "source_experiment": "EXP03_more_conv_blocks",
        "source_best_epoch": 120,
        "source_best_validation_micro_dice": 0.6850094199180603,
        "config": str(CONFIG),
        "output_root": str(OUTPUT_ROOT),
        "resume": resume,
        "command": command,
    })

    log_path = OUTPUT_ROOT / "runner.log"
    with log_path.open("a", encoding="utf-8") as log:
        header = f"\n[{now()}] command={chr(32).join(command)}\n"
        print(header, end="")
        log.write(header)
        log.flush()
        process = subprocess.Popen(command, cwd=PROJECT_ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            log.write(line)
            log.flush()
        return process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
