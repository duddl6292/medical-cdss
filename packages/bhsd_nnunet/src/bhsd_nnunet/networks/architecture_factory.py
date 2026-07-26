from __future__ import annotations

import copy
import pydoc
from typing import Any

import torch
from torch import nn
from dynamic_network_architectures.architectures.unet import (
    PlainConvUNet,
    ResidualEncoderUNet,
)


class StageAttention2d(nn.Module):
    """Lightweight spatial-channel gate applied to selected encoder skips."""

    def __init__(self, channels: int, reduction: int = 16):
        super().__init__()
        hidden = max(channels // reduction, 8)
        self.gate = nn.Sequential(
            nn.Conv2d(channels, hidden, kernel_size=1, bias=True),
            nn.LeakyReLU(negative_slope=0.01, inplace=True),
            nn.Conv2d(hidden, channels, kernel_size=1, bias=True),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * (1.0 + self.gate(x))


class StageAttentionPlainConvUNet(PlainConvUNet):
    def __init__(self, *args, attention_stages=(3, 4, 5), **kwargs):
        super().__init__(*args, **kwargs)
        features = list(self.encoder.output_channels)
        self.attention_stages = tuple(int(i) for i in attention_stages)
        invalid = [i for i in self.attention_stages if i < 0 or i >= len(features) - 1]
        if invalid:
            raise ValueError(f"Invalid attention stages: {invalid}")
        self.stage_attention = nn.ModuleDict(
            {str(i): StageAttention2d(features[i]) for i in self.attention_stages}
        )

    def forward(self, x: torch.Tensor):
        skips = self.encoder(x)
        for stage in self.attention_stages:
            skips[stage] = self.stage_attention[str(stage)](skips[stage])
        return self.decoder(skips)


def _resolved_plan_kwargs(configuration_manager) -> dict[str, Any]:
    kwargs = copy.deepcopy(configuration_manager.network_arch_init_kwargs)
    for key in configuration_manager.network_arch_init_kwargs_req_import:
        value = kwargs.get(key)
        if value is not None and isinstance(value, str):
            resolved = pydoc.locate(value)
            if resolved is None:
                raise ImportError(f"Unable to resolve architecture argument {key}={value}")
            kwargs[key] = resolved
    return kwargs


def build_bhsd_network(
    architecture_name: str,
    configuration_manager,
    num_input_channels: int,
    num_output_channels: int,
    enable_deep_supervision: bool,
):
    kwargs = _resolved_plan_kwargs(configuration_manager)
    kwargs["deep_supervision"] = enable_deep_supervision
    kwargs["input_channels"] = num_input_channels
    kwargs["num_classes"] = num_output_channels

    if architecture_name == "residual_encoder_unet":
        kwargs["n_blocks_per_stage"] = kwargs.pop("n_conv_per_stage")
        network = ResidualEncoderUNet(**kwargs)
    elif architecture_name == "stage_attention_unet":
        kwargs["attention_stages"] = (3, 4, 5)
        network = StageAttentionPlainConvUNet(**kwargs)
    elif architecture_name == "more_conv_blocks_unet":
        n_stages = int(kwargs["n_stages"])
        kwargs["n_conv_per_stage"] = [3] * n_stages
        kwargs["n_conv_per_stage_decoder"] = [3] * (n_stages - 1)
        network = PlainConvUNet(**kwargs)
    elif architecture_name == "dropout_unet":
        kwargs["dropout_op"] = nn.Dropout2d
        kwargs["dropout_op_kwargs"] = {"p": 0.2, "inplace": False}
        network = PlainConvUNet(**kwargs)
    else:
        raise ValueError(f"Unsupported BHSD architecture: {architecture_name}")

    if hasattr(network, "initialize"):
        network.apply(network.initialize)
    return network
