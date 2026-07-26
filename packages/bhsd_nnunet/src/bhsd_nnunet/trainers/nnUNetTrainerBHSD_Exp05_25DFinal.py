
import json
import math
import os

import numpy as np
import torch
import torch.nn.functional as F

from torch import autocast, nn

from batchgenerators.dataloading.single_threaded_augmenter import (
    SingleThreadedAugmenter,
)
from batchgenerators.dataloading.nondet_multi_threaded_augmenter import (
    NonDetMultiThreadedAugmenter,
)
from batchgenerators.utilities.file_and_folder_operations import (
    join,
    load_pickle,
)

from nnunetv2.training.dataloading.data_loader import (
    nnUNetDataLoader,
)
from nnunetv2.training.dataloading.nnunet_dataset import (
    infer_dataset_class,
)
from nnunetv2.utilities.default_n_proc_DA import (
    get_allowed_n_proc_DA,
)
from nnunetv2.utilities.helpers import dummy_context

from nnunetv2.training.loss.deep_supervision import (
    DeepSupervisionWrapper,
)

from nnunetv2.training.lr_scheduler.polylr import (
    PolyLRScheduler,
)

from nnunetv2.training.loss.compound_losses import (
    DC_and_CE_loss,
)

from nnunetv2.training.loss.dice import (
    MemoryEfficientSoftDiceLoss,
)

from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import (
    nnUNetTrainer,
)

from nnunetv2.utilities.collate_outputs import (
    collate_outputs,
)


# ============================================================
# Foreground Tversky Loss
# ============================================================

class ForegroundTverskyLoss(nn.Module):

    def __init__(
        self,
        alpha=0.3,
        beta=0.7,
        smooth=1e-5,
        batch_dice=True,
    ):
        super().__init__()

        # False Positive 가중치
        self.alpha = float(alpha)

        # False Negative 가중치
        self.beta = float(beta)

        self.smooth = float(smooth)
        self.batch_dice = bool(batch_dice)


    def forward(
        self,
        net_output,
        target,
    ):
        probabilities = torch.softmax(
            net_output,
            dim=1,
        )

        # target shape:
        # [B, 1, H, W] → [B, H, W]
        if (
            target.ndim == net_output.ndim
            and target.shape[1] == 1
        ):
            target = target[:, 0]

        # One-hot target인 경우 label map으로 변경
        elif (
            target.ndim == net_output.ndim
            and target.shape[1] == net_output.shape[1]
        ):
            target = torch.argmax(
                target,
                dim=1,
            )

        target = target.long()

        target_one_hot = F.one_hot(
            target,
            num_classes=net_output.shape[1],
        )

        target_one_hot = target_one_hot.movedim(
            -1,
            1,
        ).float()

        # 배경 채널 0을 제외하고 출혈 채널만 계산
        probabilities = probabilities[:, 1:]
        target_one_hot = target_one_hot[:, 1:]

        if self.batch_dice:

            axes = (
                0,
            ) + tuple(
                range(
                    2,
                    probabilities.ndim,
                )
            )

        else:

            axes = tuple(
                range(
                    2,
                    probabilities.ndim,
                )
            )

        true_positive = (
            probabilities
            * target_one_hot
        ).sum(axes)

        false_positive = (
            probabilities
            * (1.0 - target_one_hot)
        ).sum(axes)

        false_negative = (
            (1.0 - probabilities)
            * target_one_hot
        ).sum(axes)

        tversky_score = (
            true_positive
            + self.smooth
        ) / (
            true_positive
            + self.alpha * false_positive
            + self.beta * false_negative
            + self.smooth
        )

        return -tversky_score.mean()


# ============================================================
# Tversky + Cross Entropy Loss
# ============================================================

class TverskyAndCrossEntropyLoss(nn.Module):

    def __init__(
        self,
        alpha,
        beta,
        weight_tversky,
        weight_ce,
        batch_dice,
    ):
        super().__init__()

        self.tversky = ForegroundTverskyLoss(
            alpha=alpha,
            beta=beta,
            smooth=1e-5,
            batch_dice=batch_dice,
        )

        self.cross_entropy = (
            nn.CrossEntropyLoss()
        )

        self.weight_tversky = float(
            weight_tversky
        )

        self.weight_ce = float(
            weight_ce
        )


    def forward(
        self,
        net_output,
        target,
    ):
        if (
            target.ndim == net_output.ndim
            and target.shape[1] == 1
        ):

            target_ce = target[:, 0].long()

        else:

            target_ce = target.long()

        tversky_loss = self.tversky(
            net_output,
            target,
        )

        ce_loss = self.cross_entropy(
            net_output,
            target_ce,
        )

        return (
            self.weight_tversky
            * tversky_loss
            + self.weight_ce
            * ce_loss
        )


# ============================================================
# Exp05_25D Optuna Trainer
# 기본 nnUNetTrainer 직접 상속
# ============================================================

class nnUNetTrainerBHSD_Exp05_25DOptuna(
    nnUNetTrainer
):

    def __init__(
        self,
        plans,
        configuration,
        fold,
        dataset_json,
        device=torch.device("cuda"),
    ):
        # 기본 nnUNetTrainer 초기화
        super().__init__(
            plans=plans,
            configuration=configuration,
            fold=fold,
            dataset_json=dataset_json,
            device=device,
        )


        # ----------------------------------------------------
        # Exp05_25D Trial 설정 JSON 불러오기
        # ----------------------------------------------------

        config_path = os.environ.get(
            "BHSD_CONFIG_PATH"
        )

        if (
            not config_path
            or not os.path.isfile(config_path)
        ):
            raise FileNotFoundError(
                "BHSD_CONFIG_PATH 환경변수 또는 "
                "Exp05_25D 설정 JSON을 찾을 수 없습니다."
            )

        with open(
            config_path,
            "r",
            encoding="utf-8",
        ) as file:

            self.exp03_config = json.load(
                file
            )


        self.exp03_status_path = (
            os.environ.get(
                "BHSD_STATUS_PATH"
            )
        )


        # ----------------------------------------------------
        # 학습량 설정
        # ----------------------------------------------------

        self.num_epochs = int(
            self.exp03_config[
                "num_epochs"
            ]
        )

        self.num_iterations_per_epoch = int(
            self.exp03_config[
                "num_iterations_per_epoch"
            ]
        )

        self.num_val_iterations_per_epoch = int(
            self.exp03_config[
                "num_val_iterations_per_epoch"
            ]
        )


        # ----------------------------------------------------
        # Early Stopping 설정
        # ----------------------------------------------------

        self.early_stopping_min_epochs = int(
            self.exp03_config[
                "early_stopping_min_epochs"
            ]
        )

        self.early_stopping_patience = int(
            self.exp03_config[
                "early_stopping_patience"
            ]
        )

        self.early_stopping_min_delta = float(
            self.exp03_config[
                "early_stopping_min_delta"
            ]
        )


        # Early Stopping 상태값
        self.early_stopping_best_score = None
        self.early_stopping_best_epoch = None
        self.early_stopping_wait = 0
        self.early_stopping_triggered = False


        # ----------------------------------------------------
        # Optimizer 및 Learning Rate 설정
        # ----------------------------------------------------

        self.initial_lr = float(
            self.exp03_config[
                "initial_lr"
            ]
        )

        self.weight_decay = float(
            self.exp03_config[
                "weight_decay"
            ]
        )

        self.optimizer_name = (
            self.exp03_config[
                "optimizer"
            ]
        )

        self.scheduler_name = (
            self.exp03_config[
                "scheduler"
            ]
        )


        # ----------------------------------------------------
        # Loss 설정
        # ----------------------------------------------------

        self.loss_name = (
            self.exp03_config[
                "loss_name"
            ]
        )


        # ----------------------------------------------------
        # Foreground Oversampling 설정
        # ----------------------------------------------------

        self.oversample_foreground_percent = float(
            self.exp03_config[
                "oversample_foreground_percent"
            ]
        )

        self.positive_case_ratio = float(
            self.exp03_config[
                "positive_case_ratio"
            ]
        )

        self.gradient_accumulation_steps = int(
            self.exp03_config.get(
                "gradient_accumulation_steps",
                1,
            )
        )

        if self.gradient_accumulation_steps < 1:
            raise ValueError(
                "gradient_accumulation_steps는 1 이상이어야 합니다."
            )

        if (
            self.num_iterations_per_epoch
            % self.gradient_accumulation_steps
            != 0
        ):
            raise ValueError(
                "num_iterations_per_epoch은 "
                "gradient_accumulation_steps의 배수여야 합니다."
            )

        self._gradient_accumulation_counter = 0


        # ----------------------------------------------------
        # Patch size 및 Batch size 설정
        # initialize() 실행 전에 변경해야 한다.
        # ----------------------------------------------------

        self.configuration_manager.configuration[
            "patch_size"
        ] = [
            int(value)
            for value in self.exp03_config[
                "patch_size"
            ]
        ]

        self.configuration_manager.configuration[
            "batch_size"
        ] = int(
            self.exp03_config[
                "batch_size"
            ]
        )


        # ----------------------------------------------------
        # Validation 및 Optuna 상태
        # ----------------------------------------------------

        self.exp03_validation_recall = (
            float("nan")
        )

        self.exp03_best_objective = None


        # ----------------------------------------------------
        # Checkpoint 저장 간격
        # ----------------------------------------------------

        self.is_optuna_trial = bool(
            self.exp03_config.get(
                "skip_actual_validation",
                False,
            )
        )

        if self.is_optuna_trial:

            # 짧은 Trial에서는 checkpoint_latest를 저장하지 않는다.
            # checkpoint_best는 기본 Trainer가 계속 관리한다.
            self.save_every = max(
                self.num_epochs + 1,
                9999,
            )

        else:

            # 최종 모델은 중단 후 이어서 학습할 수 있도록
            # 25 epoch마다 checkpoint_latest를 저장한다.
            self.save_every = 25



    # ========================================================
    # 출혈/정상 case-level 균형 DataLoader
    # ========================================================

    @staticmethod
    def _is_foreground_location_key(class_or_region):

        if isinstance(
            class_or_region,
            (tuple, list),
        ):
            values = [
                int(value)
                for value in class_or_region
            ]
            return (
                -1 not in values
                and any(value > 0 for value in values)
            )

        try:
            return int(class_or_region) > 0
        except (TypeError, ValueError):
            return False


    def _build_case_sampling_probabilities(
        self,
        dataset_tr,
    ):
        case_identifiers = list(
            dataset_tr.identifiers
        )

        positive_flags = []

        for case_identifier in case_identifiers:
            properties = load_pickle(
                join(
                    self.preprocessed_dataset_folder,
                    f"{case_identifier}.pkl",
                )
            )

            class_locations = properties[
                "class_locations"
            ]

            has_foreground = any(
                self._is_foreground_location_key(
                    class_or_region
                )
                and len(locations) > 0
                for class_or_region, locations
                in class_locations.items()
            )

            positive_flags.append(
                has_foreground
            )

        positive_flags = np.asarray(
            positive_flags,
            dtype=bool,
        )

        positive_count = int(
            positive_flags.sum()
        )
        negative_count = int(
            (~positive_flags).sum()
        )

        probabilities = np.zeros(
            len(case_identifiers),
            dtype=np.float64,
        )

        probabilities[positive_flags] = (
            self.positive_case_ratio
            / positive_count
        )

        probabilities[~positive_flags] = (
            (1.0 - self.positive_case_ratio)
            / negative_count
        )

        self.print_to_log_file(
            "Case-level sampling: "
            f"positive={positive_count}, "
            f"negative={negative_count}, "
            f"positive_ratio="
            f"{self.positive_case_ratio:.2f}"
        )

        return probabilities


    def get_dataloaders(self):

        if self.dataset_class is None:
            self.dataset_class = (
                infer_dataset_class(
                    self.preprocessed_dataset_folder
                )
            )

        patch_size = (
            self.configuration_manager.patch_size
        )

        deep_supervision_scales = (
            self._get_deep_supervision_scales()
        )

        (
            rotation_for_DA,
            do_dummy_2d_data_aug,
            initial_patch_size,
            mirror_axes,
        ) = (
            self
            .configure_rotation_dummyDA_mirroring_and_inital_patch_size()
        )

        tr_transforms = self.get_training_transforms(
            patch_size,
            rotation_for_DA,
            deep_supervision_scales,
            mirror_axes,
            do_dummy_2d_data_aug,
            use_mask_for_norm=(
                self.configuration_manager
                .use_mask_for_norm
            ),
            is_cascaded=self.is_cascaded,
            foreground_labels=(
                self.label_manager
                .foreground_labels
            ),
            regions=(
                self.label_manager
                .foreground_regions
                if self.label_manager.has_regions
                else None
            ),
            ignore_label=(
                self.label_manager
                .ignore_label
            ),
        )

        val_transforms = self.get_validation_transforms(
            deep_supervision_scales,
            is_cascaded=self.is_cascaded,
            foreground_labels=(
                self.label_manager
                .foreground_labels
            ),
            regions=(
                self.label_manager
                .foreground_regions
                if self.label_manager.has_regions
                else None
            ),
            ignore_label=(
                self.label_manager
                .ignore_label
            ),
        )

        dataset_tr, dataset_val = (
            self.get_tr_and_val_datasets()
        )

        train_sampling_probabilities = (
            self
            ._build_case_sampling_probabilities(
                dataset_tr
            )
        )

        dl_tr = nnUNetDataLoader(
            dataset_tr,
            self.batch_size,
            initial_patch_size,
            self.configuration_manager.patch_size,
            self.label_manager,
            oversample_foreground_percent=0.0,
            sampling_probabilities=(
                train_sampling_probabilities
            ),
            pad_sides=None,
            transforms=tr_transforms,
            probabilistic_oversampling=False,
        )

        dl_val = nnUNetDataLoader(
            dataset_val,
            self.batch_size,
            self.configuration_manager.patch_size,
            self.configuration_manager.patch_size,
            self.label_manager,
            oversample_foreground_percent=0.0,
            sampling_probabilities=None,
            pad_sides=None,
            transforms=val_transforms,
            probabilistic_oversampling=False,
        )

        allowed_num_processes = (
            get_allowed_n_proc_DA()
        )

        if allowed_num_processes == 0:
            train_augmenter = (
                SingleThreadedAugmenter(
                    dl_tr,
                    None,
                )
            )
            validation_augmenter = (
                SingleThreadedAugmenter(
                    dl_val,
                    None,
                )
            )

        else:
            train_augmenter = (
                NonDetMultiThreadedAugmenter(
                    data_loader=dl_tr,
                    transform=None,
                    num_processes=(
                        allowed_num_processes
                    ),
                    num_cached=max(
                        6,
                        allowed_num_processes // 2,
                    ),
                    seeds=None,
                    pin_memory=(
                        self.device.type == "cuda"
                    ),
                    wait_time=0.002,
                )
            )

            validation_augmenter = (
                NonDetMultiThreadedAugmenter(
                    data_loader=dl_val,
                    transform=None,
                    num_processes=max(
                        1,
                        allowed_num_processes // 2,
                    ),
                    num_cached=max(
                        3,
                        allowed_num_processes // 4,
                    ),
                    seeds=None,
                    pin_memory=(
                        self.device.type == "cuda"
                    ),
                    wait_time=0.002,
                )
            )

        _ = next(train_augmenter)
        _ = next(validation_augmenter)

        return (
            train_augmenter,
            validation_augmenter,
        )

    # ========================================================
    # Loss 생성
    # ========================================================

    def _build_loss(self):

        if self.loss_name == "dice_ce":

            loss = DC_and_CE_loss(
                {
                    "batch_dice":
                        self.configuration_manager.batch_dice,

                    "smooth": 1e-5,

                    "do_bg": False,

                    "ddp": self.is_ddp,
                },
                {},
                weight_ce=float(
                    self.exp03_config[
                        "weight_ce"
                    ]
                ),
                weight_dice=float(
                    self.exp03_config[
                        "weight_overlap"
                    ]
                ),
                ignore_label=(
                    self.label_manager.ignore_label
                ),
                dice_class=(
                    MemoryEfficientSoftDiceLoss
                ),
            )


        elif self.loss_name == "tversky_ce":

            if (
                self.label_manager.has_regions
                or self.label_manager.ignore_label
                is not None
            ):
                raise RuntimeError(
                    "현재 BHSD Exp05_25D Tversky Loss는 "
                    "일반 binary label 0/1 전용입니다."
                )

            loss = (
                TverskyAndCrossEntropyLoss(
                    alpha=float(
                        self.exp03_config[
                            "tversky_alpha"
                        ]
                    ),
                    beta=float(
                        self.exp03_config[
                            "tversky_beta"
                        ]
                    ),
                    weight_tversky=float(
                        self.exp03_config[
                            "weight_overlap"
                        ]
                    ),
                    weight_ce=float(
                        self.exp03_config[
                            "weight_ce"
                        ]
                    ),
                    batch_dice=(
                        self.configuration_manager.batch_dice
                    ),
                )
            )


        else:

            raise ValueError(
                "지원하지 않는 Loss: "
                f"{self.loss_name}"
            )


        # Deep Supervision 적용
        if self.enable_deep_supervision:

            scales = (
                self._get_deep_supervision_scales()
            )

            weights = np.array([
                1 / (2 ** index)
                for index in range(
                    len(scales)
                )
            ])

            weights[-1] = 0

            weights = (
                weights
                / weights.sum()
            )

            loss = DeepSupervisionWrapper(
                loss,
                weights,
            )

        return loss


    # ========================================================
    # Optimizer 및 Scheduler 생성
    # ========================================================

    def configure_optimizers(self):

        if self.optimizer_name == "sgd":

            optimizer = torch.optim.SGD(
                self.network.parameters(),
                lr=self.initial_lr,
                momentum=0.99,
                nesterov=True,
                weight_decay=self.weight_decay,
            )


        elif self.optimizer_name == "adamw":

            optimizer = torch.optim.AdamW(
                self.network.parameters(),
                lr=self.initial_lr,
                weight_decay=self.weight_decay,
            )


        else:

            raise ValueError(
                "지원하지 않는 Optimizer: "
                f"{self.optimizer_name}"
            )


        if self.scheduler_name == "poly":

            scheduler = PolyLRScheduler(
                optimizer,
                self.initial_lr,
                self.num_epochs,
            )


        elif self.scheduler_name == "cosine":

            scheduler = (
                torch.optim.lr_scheduler
                .CosineAnnealingLR(
                    optimizer,
                    T_max=self.num_epochs,
                    eta_min=(
                        self.initial_lr
                        * 0.01
                    ),
                )
            )


        else:

            raise ValueError(
                "지원하지 않는 Scheduler: "
                f"{self.scheduler_name}"
            )

        return optimizer, scheduler


    # ========================================================
    # Gradient Accumulation
    # ========================================================

    def train_step(self, batch):

        data = batch["data"]
        target = batch["target"]

        data = data.to(
            self.device,
            non_blocking=True,
        )

        if isinstance(target, list):
            target = [
                item.to(
                    self.device,
                    non_blocking=True,
                )
                for item in target
            ]
        else:
            target = target.to(
                self.device,
                non_blocking=True,
            )

        accumulation_index = (
            self._gradient_accumulation_counter
            % self.gradient_accumulation_steps
        )

        if accumulation_index == 0:
            self.optimizer.zero_grad(
                set_to_none=True
            )

        with (
            autocast(
                self.device.type,
                enabled=True,
            )
            if self.device.type == "cuda"
            else dummy_context()
        ):
            output = self.network(data)
            loss = self.loss(
                output,
                target,
            )
            scaled_loss = (
                loss
                / self.gradient_accumulation_steps
            )

        should_step = (
            accumulation_index
            == self.gradient_accumulation_steps - 1
        )

        if self.grad_scaler is not None:
            self.grad_scaler.scale(
                scaled_loss
            ).backward()

            if should_step:
                self.grad_scaler.unscale_(
                    self.optimizer
                )
                torch.nn.utils.clip_grad_norm_(
                    self.network.parameters(),
                    12,
                )
                self.grad_scaler.step(
                    self.optimizer
                )
                self.grad_scaler.update()
        else:
            scaled_loss.backward()

            if should_step:
                torch.nn.utils.clip_grad_norm_(
                    self.network.parameters(),
                    12,
                )
                self.optimizer.step()

        self._gradient_accumulation_counter += 1

        return {
            "loss":
                loss.detach().cpu().numpy()
        }


    # ========================================================
    # 학습 시작
    # ========================================================

    def on_train_start(self):

        super().on_train_start()

        # 이어서 학습할 때 기본 nnU-Net checkpoint의
        # _best_ema 값을 Early Stopping 기준값으로 사용한다.
        if (
            self.early_stopping_best_score
            is None
            and self._best_ema is not None
        ):
            self.early_stopping_best_score = float(
                self._best_ema
            )

            self.early_stopping_best_epoch = int(
                self.current_epoch
            )

        self.print_to_log_file(
            "=" * 70
        )

        self.print_to_log_file(
            "[Exp05_25D Early Stopping 설정]"
        )

        self.print_to_log_file(
            f"Maximum epochs: "
            f"{self.num_epochs}"
        )

        self.print_to_log_file(
            f"Minimum epochs: "
            f"{self.early_stopping_min_epochs}"
        )

        self.print_to_log_file(
            f"Patience: "
            f"{self.early_stopping_patience}"
        )

        self.print_to_log_file(
            "Gradient accumulation steps: "
            f"{self.gradient_accumulation_steps}"
        )

        self.print_to_log_file(
            "Effective batch size: "
            f"{self.batch_size * self.gradient_accumulation_steps}"
        )

        self.print_to_log_file(
            f"Minimum delta: "
            f"{self.early_stopping_min_delta}"
        )

        self.print_to_log_file(
            "=" * 70
        )


    # ========================================================
    # Validation Recall 계산
    # ========================================================

    def on_validation_epoch_end(
        self,
        val_outputs,
    ):
        # 기본 nnU-Net Validation Dice 및 Loss 계산
        super().on_validation_epoch_end(
            val_outputs
        )

        outputs = collate_outputs(
            val_outputs
        )

        true_positive = np.sum(
            outputs["tp_hard"],
            axis=0,
        )

        false_negative = np.sum(
            outputs["fn_hard"],
            axis=0,
        )

        recall_per_class = (
            true_positive
            / np.maximum(
                true_positive
                + false_negative,
                1e-8,
            )
        )

        self.exp03_validation_recall = float(
            np.nanmean(
                recall_per_class
            )
        )


    # ========================================================
    # Trial 상태 JSONL 저장
    # ========================================================

    def _append_exp03_status(
        self,
        payload,
    ):
        if not self.exp03_status_path:
            return

        status_parent_dir = os.path.dirname(
            self.exp03_status_path
        )

        if status_parent_dir:

            os.makedirs(
                status_parent_dir,
                exist_ok=True,
            )

        with open(
            self.exp03_status_path,
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                )
                + "\n"
            )


    # ========================================================
    # Epoch 종료 및 Early Stopping
    # ========================================================

    def on_epoch_end(self):

        # 기본 nnU-Net 처리
        #
        # - Loss 출력
        # - EMA foreground Dice 갱신
        # - checkpoint_best 저장
        # - checkpoint_latest 저장
        # - current_epoch 증가
        super().on_epoch_end()


        completed_epochs = int(
            self.current_epoch
        )

        ema_dice = float(
            self.logger.get_value(
                "ema_fg_dice",
                step=-1,
            )
        )

        recall = float(
            self.exp03_validation_recall
        )


        if not math.isfinite(recall):

            recall = 0.0


        if math.isfinite(ema_dice):

            objective = ema_dice

        else:

            objective = -1.0


        if (
            self.exp03_best_objective
            is None
            or objective
            > self.exp03_best_objective
        ):

            self.exp03_best_objective = (
                objective
            )


        # ----------------------------------------------------
        # Early Stopping 개선 여부
        # ----------------------------------------------------

        improved = False

        if not math.isfinite(
            ema_dice
        ):

            self.early_stopping_wait += 1


        elif (
            self.early_stopping_best_score
            is None
        ):

            self.early_stopping_best_score = (
                ema_dice
            )

            self.early_stopping_best_epoch = (
                completed_epochs
            )

            self.early_stopping_wait = 0

            improved = True


        elif (
            ema_dice
            >
            self.early_stopping_best_score
            + self.early_stopping_min_delta
        ):

            self.early_stopping_best_score = (
                ema_dice
            )

            self.early_stopping_best_epoch = (
                completed_epochs
            )

            self.early_stopping_wait = 0

            improved = True


        else:

            self.early_stopping_wait += 1


        self.print_to_log_file(
            (
                "[Exp05_25D Early Stopping] "
                f"Epoch={completed_epochs}, "
                f"EMA Dice={ema_dice:.6f}, "
                f"Recall={recall:.6f}, "
                f"Wait="
                f"{self.early_stopping_wait}/"
                f"{self.early_stopping_patience}, "
                f"Improved={improved}"
            )
        )


        # ----------------------------------------------------
        # Early Stopping 실행 조건
        # ----------------------------------------------------

        minimum_epochs_completed = (
            completed_epochs
            >= self.early_stopping_min_epochs
        )

        patience_exceeded = (
            self.early_stopping_wait
            >= self.early_stopping_patience
        )


        if (
            minimum_epochs_completed
            and patience_exceeded
        ):

            self.early_stopping_triggered = True

            self.print_to_log_file(
                (
                    "[Exp05_25D Early Stopping 발생] "
                    f"Best Epoch="
                    f"{self.early_stopping_best_epoch}, "
                    f"Best EMA Dice="
                    f"{self.early_stopping_best_score}"
                )
            )


        # ----------------------------------------------------
        # Optuna status 저장
        # ----------------------------------------------------

        self._append_exp03_status({
            "completed_epochs":
                completed_epochs,

            "ema_fg_dice":
                ema_dice,

            "foreground_recall":
                recall,

            "objective":
                objective,

            "best_objective":
                self.exp03_best_objective,

            "early_stopping_triggered":
                bool(
                    self.early_stopping_triggered
                ),
        })


    # ========================================================
    # Early Stopping이 포함된 학습 반복
    # ========================================================

    def run_training(self):

        self.on_train_start()

        for epoch in range(
            self.current_epoch,
            self.num_epochs,
        ):
            self.on_epoch_start()

            # Training
            self.on_train_epoch_start()

            train_outputs = []

            for batch_id in range(
                self.num_iterations_per_epoch
            ):
                train_outputs.append(
                    self.train_step(
                        next(
                            self.dataloader_train
                        )
                    )
                )

            self.on_train_epoch_end(
                train_outputs
            )


            # Validation
            with torch.no_grad():

                self.on_validation_epoch_start()

                val_outputs = []

                for batch_id in range(
                    self.num_val_iterations_per_epoch
                ):
                    val_outputs.append(
                        self.validation_step(
                            next(
                                self.dataloader_val
                            )
                        )
                    )

                self.on_validation_epoch_end(
                    val_outputs
                )


            # Epoch 종료
            self.on_epoch_end()


            if self.early_stopping_triggered:

                self.print_to_log_file(
                    "Exp05_25D Early Stopping 조건으로 "
                    "학습 반복을 종료합니다."
                )

                break


        # checkpoint_final 저장 및 정리
        self.on_train_end()


    # ========================================================
    # Trial에서는 전체 Validation 추론 생략
    # ========================================================

    def perform_actual_validation(
        self,
        save_probabilities=False,
    ):
        if self.is_optuna_trial:

            self.print_to_log_file(
                "Exp05_25D Optuna Trial: "
                "full validation inference skipped."
            )

            return

        return super().perform_actual_validation(
            save_probabilities
        )


# ============================================================
# Exp05_25D 최종 모델
# Exp05_25D Optuna Trainer 설정을 그대로 상속
# ============================================================

class nnUNetTrainerBHSD_Exp05_25DFinal(
    nnUNetTrainerBHSD_Exp05_25DOptuna
):
    pass
