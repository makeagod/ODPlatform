# -*- coding: utf-8 -*-
"""D7 验证服务用的 build_val_config(config, merger) 接口。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from odp_platform.common.provenance_adapter import ProvenanceMergerAdapter
from odp_platform.runtime_config.builder import build_config
from odp_platform.runtime_config.val import YOLOValConfig


def build_val_config(
    yaml_path: Union[str, Path, None] = None,
    cli_args: Optional[Dict[str, Any]] = None,
) -> Tuple[YOLOValConfig, ProvenanceMergerAdapter]:
    """加载 val 配置并返回 Pydantic 模型 + 溯源适配器（课程 D7 API）。"""
    rc = build_config(
        "val",
        yaml_path=yaml_path,
        cli_overrides=cli_args,
    )
    config = rc.to_yolo_config()
    if not isinstance(config, YOLOValConfig):
        raise TypeError(f"期望 YOLOValConfig，实际 {type(config).__name__}")
    return config, ProvenanceMergerAdapter(rc.provenance)
