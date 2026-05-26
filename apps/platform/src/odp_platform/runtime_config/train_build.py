# -*- coding: utf-8 -*-
"""D6 训练服务用的 build_train_config(config, merger) 接口。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from odp_platform.common.provenance_adapter import ProvenanceMergerAdapter
from odp_platform.runtime_config.builder import build_config
from odp_platform.runtime_config.train import YOLOTrainConfig


def build_train_config(
    yaml_path: Union[str, Path, None] = None,
    cli_args: Optional[Dict[str, Any]] = None,
) -> Tuple[YOLOTrainConfig, ProvenanceMergerAdapter]:
    """加载 train 配置并返回 Pydantic 模型 + 溯源适配器（课程 D6 API）。"""
    rc = build_config(
        "train",
        yaml_path=yaml_path,
        cli_overrides=cli_args,
    )
    config = rc.to_yolo_config()
    if not isinstance(config, YOLOTrainConfig):
        raise TypeError(f"期望 YOLOTrainConfig，实际 {type(config).__name__}")
    return config, ProvenanceMergerAdapter(rc.provenance)
