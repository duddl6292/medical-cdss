#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SWEEP_CONFIG = PROJECT_ROOT / "training/configs/architecture_sweep.json"
TRAINER_DIR = PROJECT_ROOT / "packages/bhsd_nnunet/src/bhsd_nnunet/trainers"


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def locate_model_dir(experiment_root: Path, trainer: str, fold: int):
    expected = (
        experiment_root
        / "Dataset001_BHSD_25D"
        / f"{trainer}__nnUNetPlans__2d"
        / f"fold_{fold}"
    )
    if expected.is_dir():
        return expected
    matches = list(experiment_root.glob(f"Dataset*/{trainer}__*/fold_{fold}"))
    return matches[0] if matches else expected


def ensure_resume_checkpoint(model_dir: Path):
    latest = model_dir / "checkpoint_latest.pth"
    best = model_dir / "checkpoint_best.pth"
    if latest.is_file() and latest.stat().st_size > 0:
        return True
    if best.is_file() and best.stat().st_size > 0:
        model_dir.mkdir(parents=True, exist_ok=True)
        tmp = latest.with_suffix(".pth.tmp")
        shutil.copy2(best, tmp)
        os.replace(tmp, latest)
        return True
    return False


def read_metrics(model_dir: Path):
    path = model_dir / "validation_metrics.json"
    return load_json(path) if path.is_file() else {}


def write_summary(output_root: Path, manifest):
    rows = []
    for exp_id, state in manifest["experiments"].items():
        metrics = state.get("metrics", {})
        rows.append(
            {
                "experiment_id": exp_id,
                "trainer": state.get("trainer"),
                "status": state.get("status"),
                "attempts": state.get("attempts", 0),
                "best_epoch": metrics.get("best_epoch"),
                "validation_micro_dice": metrics.get("best_validation_micro_dice"),
                "last_error": state.get("last_error"),
                "result_dir": state.get("result_dir"),
            }
        )
    csv_path = output_root / "sweep_summary.csv"
    tmp = csv_path.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys() if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    os.replace(tmp, csv_path)


def main():
    parser = argparse.ArgumentParser(description="Run four BHSD architecture experiments sequentially.")
    parser.add_argument("--config", type=Path, default=DEFAULT_SWEEP_CONFIG)
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()

    sweep_path = args.config.resolve()
    sweep = load_json(sweep_path)
    common_config = (PROJECT_ROOT / sweep["common_config"]).resolve()
    if not common_config.is_file():
        raise FileNotFoundError(common_config)

    output_root = Path(sweep["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    free_gb = shutil.disk_usage(output_root).free / (1024 ** 3)
    required_gb = float(sweep.get("minimum_free_disk_gb", 8))
    if free_gb < required_gb:
        raise RuntimeError(f"Only {free_gb:.1f} GiB free; {required_gb:.1f} GiB required.")

    manifest_path = output_root / "sweep_manifest.json"
    manifest = load_json(manifest_path) if manifest_path.is_file() else {
        "created_at": utc_now(),
        "sweep_config": str(sweep_path),
        "experiments": {},
    }
    for exp in sweep["experiments"]:
        manifest["experiments"].setdefault(
            exp["id"],
            {
                "trainer": exp["trainer"],
                "status": "pending",
                "attempts": 0,
                "result_dir": str(output_root / exp["id"]),
            },
        )
    atomic_json(manifest_path, manifest)

    child = None

    def stop_child(signum, _frame):
        nonlocal child
        if child is not None and child.poll() is None:
            child.terminate()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, stop_child)
    signal.signal(signal.SIGTERM, stop_child)

    max_retries = int(sweep.get("max_retries_per_experiment", 3))
    for exp in sweep["experiments"]:
        exp_id = exp["id"]
        trainer = exp["trainer"]
        state = manifest["experiments"][exp_id]
        experiment_root = output_root / exp_id
        model_dir = locate_model_dir(experiment_root, trainer, int(sweep["fold"]))

        if (model_dir / "checkpoint_final.pth").is_file():
            state["status"] = "completed"
            state["metrics"] = read_metrics(model_dir)
            atomic_json(manifest_path, manifest)
            write_summary(output_root, manifest)
            continue
        if state.get("status") == "failed" and not args.retry_failed:
            continue
        if state.get("status") == "failed" and args.retry_failed:
            state["attempts"] = 0
            state["status"] = "pending"

        while state.get("attempts", 0) < max_retries:
            resume = ensure_resume_checkpoint(model_dir)
            state["status"] = "running"
            state["attempts"] = int(state.get("attempts", 0)) + 1
            state["started_at"] = utc_now()
            state["resume"] = resume
            atomic_json(manifest_path, manifest)

            experiment_root.mkdir(parents=True, exist_ok=True)
            log_path = experiment_root / "runner.log"
            env = os.environ.copy()
            env.update(
                {
                    "nnUNet_raw": "/home/stu03/medical-data/nnUNet_raw",
                    "nnUNet_preprocessed": "/home/stu03/medical-data/nnUNet_preprocessed",
                    "nnUNet_results": str(experiment_root),
                    "nnUNet_extTrainer": str(TRAINER_DIR),
                    "BHSD_CONFIG_PATH": str(common_config),
                    "BHSD_STATUS_PATH": str(experiment_root / "epoch_status.jsonl"),
                    "nnUNet_compile": "false",
                    "nnUNet_n_proc_DA": "0",
                    "PYTHONUNBUFFERED": "1",
                }
            )
            command = [
                str(PROJECT_ROOT / ".venv/bin/nnUNetv2_train"),
                str(sweep["dataset_id"]),
                str(sweep["configuration"]),
                str(sweep["fold"]),
                "-tr",
                trainer,
                "-p",
                str(sweep["plans"]),
                "-device",
                "cuda",
            ]
            if resume:
                command.append("--c")

            with log_path.open("a", encoding="utf-8") as log:
                header = f"\n[{utc_now()}] attempt={state['attempts']} command={' '.join(command)}\n"
                sys.stdout.write(header)
                log.write(header)
                log.flush()
                child = subprocess.Popen(
                    command,
                    cwd=PROJECT_ROOT,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                assert child.stdout is not None
                for line in child.stdout:
                    sys.stdout.write(line)
                    log.write(line)
                    log.flush()
                return_code = child.wait()
                child = None

            if return_code == 0 and (model_dir / "checkpoint_final.pth").is_file():
                state["status"] = "completed"
                state["completed_at"] = utc_now()
                state["metrics"] = read_metrics(model_dir)
                state["last_error"] = None
                break

            state["status"] = "retrying"
            state["metrics"] = read_metrics(model_dir)
            state["last_error"] = f"training exited with code {return_code}"
            state["failed_at"] = utc_now()
            atomic_json(manifest_path, manifest)
            write_summary(output_root, manifest)
            if state["attempts"] < max_retries:
                time.sleep(5)

        if state.get("status") != "completed":
            state["status"] = "failed"
        atomic_json(manifest_path, manifest)
        write_summary(output_root, manifest)

    manifest["finished_at"] = utc_now()
    atomic_json(manifest_path, manifest)
    write_summary(output_root, manifest)
    failed = [k for k, v in manifest["experiments"].items() if v["status"] == "failed"]
    print(f"Sweep finished. Failed experiments: {failed or 'none'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
