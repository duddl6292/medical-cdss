from __future__ import annotations

import gc
import json
import math
import os
from pathlib import Path
from time import time

import numpy as np
import torch
from torch._dynamo import OptimizedModule

from batchgenerators.dataloading.single_threaded_augmenter import SingleThreadedAugmenter
from batchgenerators.utilities.file_and_folder_operations import join

from bhsd_nnunet.networks.architecture_factory import build_bhsd_network
from bhsd_nnunet.trainers.nnUNetTrainerBHSD_Exp05_25DFinal import (
    nnUNetTrainerBHSD_Exp05_25DFinal,
)


class nnUNetTrainerBHSDSweepBase(nnUNetTrainerBHSD_Exp05_25DFinal):
    ARCHITECTURE_NAME = "abstract"
    ARCHITECTURE_CHANGES = {}

    def __init__(
        self,
        plans,
        configuration,
        fold,
        dataset_json,
        device=torch.device("cuda"),
    ):
        super().__init__(
            plans=plans,
            configuration=configuration,
            fold=fold,
            dataset_json=dataset_json,
            device=device,
        )
        self.save_every = int(self.exp03_config.get("save_every", 5))
        self.validation_threshold = float(
            self.exp03_config.get("validation_threshold", 0.5)
        )
        if self.validation_threshold != 0.5:
            raise ValueError(
                "Sweep model selection requires validation_threshold=0.5. "
                "Threshold tuning belongs after model selection."
            )
        self.best_validation_micro_dice = None
        self.best_validation_epoch = None
        self.current_validation_micro_dice = float("nan")
        self._sweep_validation_loader = None

    @classmethod
    def build_network_architecture(
        cls,
        plans_manager,
        configuration_manager,
        num_input_channels,
        num_output_channels,
        enable_deep_supervision=True,
    ):
        return build_bhsd_network(
            cls.ARCHITECTURE_NAME,
            configuration_manager,
            num_input_channels,
            num_output_channels,
            enable_deep_supervision,
        )

    def get_dataloaders(self):
        train_augmenter, validation_augmenter = super().get_dataloaders()
        if not isinstance(validation_augmenter, SingleThreadedAugmenter):
            raise RuntimeError(
                "Deterministic full validation requires nnUNet_n_proc_DA=0."
            )
        loader = validation_augmenter.data_loader
        loader.infinite = False
        loader.return_incomplete = True
        loader.reset()
        self._sweep_validation_loader = loader
        self.num_val_iterations_per_epoch = len(loader.indices)
        return train_augmenter, validation_augmenter

    def on_validation_epoch_start(self):
        if self._sweep_validation_loader is not None:
            self._sweep_validation_loader.reset()
        super().on_validation_epoch_start()

    def on_validation_epoch_end(self, val_outputs):
        super().on_validation_epoch_end(val_outputs)
        self.current_validation_micro_dice = float(
            self.logger.get_value("mean_fg_dice", step=-1)
        )

    def _architecture_metadata(self):
        return {
            "experiment_name": self.ARCHITECTURE_NAME,
            "trainer_name": self.__class__.__name__,
            "input_mode": "2.5d",
            "context_slices": int(self.num_input_channels or 3),
            "convolution_dimension": "2d",
            "baseline": "PlainConvUNet Exp05",
            "changed_fields": self.ARCHITECTURE_CHANGES,
            "selection_metric": "full_validation_micro_dice",
            "selection_threshold": self.validation_threshold,
            "validation_cases": int(self.num_val_iterations_per_epoch),
            "physical_batch_size": int(self.batch_size),
            "gradient_accumulation_steps": int(self.gradient_accumulation_steps),
            "effective_batch_size": int(
                self.batch_size * self.gradient_accumulation_steps
            ),
        }

    def _atomic_write_json(self, path: Path, payload):
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp, path)

    def on_train_start(self):
        super().on_train_start()
        if self._best_ema is not None and self.best_validation_micro_dice is None:
            self.best_validation_micro_dice = float(self._best_ema)
        output = Path(self.output_folder)
        previous_metrics = output / "validation_metrics.json"
        if previous_metrics.is_file():
            stored = json.loads(previous_metrics.read_text(encoding="utf-8"))
            self.best_validation_epoch = stored.get("best_epoch")
            if self.best_validation_micro_dice is None:
                self.best_validation_micro_dice = stored.get(
                    "best_validation_micro_dice"
                )
        if self.local_rank == 0:
            output.mkdir(parents=True, exist_ok=True)
            metadata = self._architecture_metadata()
            self._atomic_write_json(output / "architecture.json", metadata)
            self._atomic_write_json(output / "experiment_config.json", self.exp03_config)
            self._atomic_write_json(
                output / "baseline_diff.json",
                {
                    "baseline": "Exp05 PlainConvUNet",
                    "changed_fields": self.ARCHITECTURE_CHANGES,
                    "unchanged_training_conditions": {
                        "optimizer": self.optimizer_name,
                        "initial_lr": self.initial_lr,
                        "weight_decay": self.weight_decay,
                        "scheduler": self.scheduler_name,
                        "loss": self.loss_name,
                        "effective_batch_size": (
                            self.batch_size * self.gradient_accumulation_steps
                        ),
                    },
                },
            )
            self.print_to_log_file(
                f"Full deterministic validation cases: {self.num_val_iterations_per_epoch}"
            )
            self.print_to_log_file(
                "Best checkpoint metric: full validation Micro Dice at threshold 0.5"
            )

    def save_checkpoint(self, filename):
        if self.local_rank != 0:
            return
        if self.disable_checkpointing:
            self.print_to_log_file("No checkpoint written, checkpointing is disabled")
            return

        gc.collect()
        if self.device.type == "cuda":
            torch.cuda.empty_cache()

        module = self.network.module if self.is_ddp else self.network
        if isinstance(module, OptimizedModule):
            module = module._orig_mod

        payload = {
            "network_weights": module.state_dict(),
            "optimizer_state": self.optimizer.state_dict(),
            "grad_scaler_state": (
                self.grad_scaler.state_dict() if self.grad_scaler is not None else None
            ),
            "logging": self.logger.get_checkpoint(),
            "_best_ema": self.best_validation_micro_dice,
            "current_epoch": self.current_epoch + 1,
            "init_args": self.my_init_kwargs,
            "trainer_name": self.__class__.__name__,
            "inference_allowed_mirroring_axes": self.inference_allowed_mirroring_axes,
            "architecture_metadata": self._architecture_metadata(),
            "best_validation_micro_dice": self.best_validation_micro_dice,
            "best_validation_epoch": self.best_validation_epoch,
            "selection_metric": "full_validation_micro_dice",
        }
        target = Path(filename)
        temporary = target.with_suffix(target.suffix + ".tmp")
        torch.save(payload, temporary)
        os.replace(temporary, target)

        del payload
        gc.collect()
        if self.device.type == "cuda":
            torch.cuda.empty_cache()

    def on_epoch_end(self):
        self.logger.log("epoch_end_timestamps", time(), self.current_epoch)
        micro_dice = float(self.current_validation_micro_dice)
        recall = float(self.exp03_validation_recall)
        if not math.isfinite(recall):
            recall = 0.0

        self.print_to_log_file(
            "train_loss",
            np.round(self.logger.get_value("train_losses", step=-1), decimals=4),
        )
        self.print_to_log_file(
            "val_loss",
            np.round(self.logger.get_value("val_losses", step=-1), decimals=4),
        )
        self.print_to_log_file(
            "Full validation Micro Dice", np.round(micro_dice, decimals=6)
        )
        self.print_to_log_file(
            "Epoch time: "
            f"{np.round(self.logger.get_value('epoch_end_timestamps', step=-1) - self.logger.get_value('epoch_start_timestamps', step=-1), decimals=2)} s"
        )

        completed_epoch = self.current_epoch + 1
        if completed_epoch % self.save_every == 0 and completed_epoch != self.num_epochs:
            self.save_checkpoint(join(self.output_folder, "checkpoint_latest.pth"))

        improved_for_checkpoint = (
            self.best_validation_micro_dice is None
            or micro_dice > self.best_validation_micro_dice
        )
        if improved_for_checkpoint:
            self.best_validation_micro_dice = micro_dice
            self.best_validation_epoch = completed_epoch
            self._best_ema = micro_dice
            self.print_to_log_file(
                f"New best full validation Micro Dice: {micro_dice:.6f}"
            )
            self.save_checkpoint(join(self.output_folder, "checkpoint_best.pth"))

        improved_for_early_stopping = (
            self.early_stopping_best_score is None
            or micro_dice
            > self.early_stopping_best_score + self.early_stopping_min_delta
        )
        if improved_for_early_stopping:
            self.early_stopping_best_score = micro_dice
            self.early_stopping_best_epoch = completed_epoch
            self.early_stopping_wait = 0
        else:
            self.early_stopping_wait += 1

        self.exp03_best_objective = max(
            micro_dice,
            self.exp03_best_objective
            if self.exp03_best_objective is not None
            else float("-inf"),
        )
        self.early_stopping_triggered = (
            completed_epoch >= self.early_stopping_min_epochs
            and self.early_stopping_wait >= self.early_stopping_patience
        )

        self.print_to_log_file(
            "[Sweep Early Stopping] "
            f"Epoch={completed_epoch}, MicroDice={micro_dice:.6f}, "
            f"Recall={recall:.6f}, Wait={self.early_stopping_wait}/"
            f"{self.early_stopping_patience}, "
            f"Triggered={self.early_stopping_triggered}"
        )
        self._append_exp03_status(
            {
                "completed_epochs": completed_epoch,
                "validation_micro_dice": micro_dice,
                "foreground_recall": recall,
                "best_validation_micro_dice": self.best_validation_micro_dice,
                "early_stopping_triggered": self.early_stopping_triggered,
                "architecture": self.ARCHITECTURE_NAME,
            }
        )

        if self.local_rank == 0:
            self.logger.plot_progress_png(self.output_folder)
            self._atomic_write_json(
                Path(self.output_folder) / "validation_metrics.json",
                {
                    "latest_epoch": completed_epoch,
                    "latest_validation_micro_dice": micro_dice,
                    "best_validation_micro_dice": self.best_validation_micro_dice,
                    "best_epoch": self.best_validation_epoch,
                    "selection_threshold": self.validation_threshold,
                },
            )
        self.current_epoch += 1


class nnUNetTrainerBHSDResidualEncoderSweep(nnUNetTrainerBHSDSweepBase):
    ARCHITECTURE_NAME = "residual_encoder_unet"
    ARCHITECTURE_CHANGES = {
        "encoder": {"before": "plain_conv", "after": "residual_basic_blocks"}
    }


class nnUNetTrainerBHSDStageAttentionSweep(nnUNetTrainerBHSDSweepBase):
    ARCHITECTURE_NAME = "stage_attention_unet"
    ARCHITECTURE_CHANGES = {
        "attention": {
            "before": "none",
            "after": "lightweight_skip_attention",
            "zero_based_encoder_stages": [3, 4, 5],
        }
    }


class nnUNetTrainerBHSDMoreConvSweep(nnUNetTrainerBHSDSweepBase):
    ARCHITECTURE_NAME = "more_conv_blocks_unet"
    ARCHITECTURE_CHANGES = {
        "conv_blocks_per_stage": {"before": 2, "after": 3}
    }


class nnUNetTrainerBHSDMoreConvFineTune(nnUNetTrainerBHSDMoreConvSweep):
    """Fine-tune EXP03 while loading every network weight, including seg heads."""

    def _architecture_metadata(self):
        metadata = super()._architecture_metadata()
        metadata["fine_tuning"] = {
            "source_checkpoint": os.environ.get("BHSD_FINETUNE_CHECKPOINT"),
            "load_scope": "all_network_weights_including_segmentation_heads",
            "optimizer_state": "new",
            "epoch_counter": "new",
        }
        return metadata

    def on_train_start(self):
        super().on_train_start()
        source = os.environ.get("BHSD_FINETUNE_CHECKPOINT")
        if not source or self.current_epoch != 0:
            return

        source_path = Path(source).resolve()
        if not source_path.is_file():
            raise FileNotFoundError(
                f"BHSD fine-tuning checkpoint does not exist: {source_path}"
            )

        checkpoint = torch.load(
            source_path,
            map_location=self.device,
            weights_only=False,
        )
        pretrained = checkpoint["network_weights"]
        module = self.network.module if self.is_ddp else self.network
        if isinstance(module, OptimizedModule):
            module = module._orig_mod

        current = module.state_dict()
        missing = sorted(set(current) - set(pretrained))
        unexpected = sorted(set(pretrained) - set(current))
        mismatched = sorted(
            key
            for key in set(current) & set(pretrained)
            if current[key].shape != pretrained[key].shape
        )
        if missing or unexpected or mismatched:
            raise RuntimeError(
                "Fine-tuning checkpoint is not an exact architecture match. "
                f"missing={missing[:5]}, unexpected={unexpected[:5]}, "
                f"shape_mismatch={mismatched[:5]}"
            )

        module.load_state_dict(pretrained, strict=True)
        self.print_to_log_file(
            "Loaded all network weights for fine-tuning from "
            f"{source_path}; optimizer and epoch counter start fresh."
        )


class nnUNetTrainerBHSDDropoutSweep(nnUNetTrainerBHSDSweepBase):
    ARCHITECTURE_NAME = "dropout_unet"
    ARCHITECTURE_CHANGES = {
        "dropout": {"before": 0.0, "after": 0.2, "type": "Dropout2d"}
    }
