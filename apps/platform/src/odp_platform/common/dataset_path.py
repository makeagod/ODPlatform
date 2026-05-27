# -*- coding: utf-8 -*-
"""解析 Ultralytics 数据集 YAML 路径。"""
from __future__ import annotations

import logging
from pathlib import Path

from odp_platform.common.paths import (
    APP_DIR,
    CONFIGS_DATASETS_DIR,
    DATASET_CONFIGS_DIR,
    dataset_yaml_path,
)

logger = logging.getLogger(__name__)


def resolve_dataset_path(data: str | Path) -> Path:
    if not data or (isinstance(data, str) and not str(data).strip()):
        raise ValueError("data 不能为空，请指定数据集 yaml 或名称（如 rsod）")

    data_path = Path(data)

    if data_path.is_absolute():
        return data_path.resolve()

    search_dirs = (
        DATASET_CONFIGS_DIR,
        CONFIGS_DATASETS_DIR,
        APP_DIR / "configs" / "datasets",
    )
    if data_path.suffix in (".yaml", ".yml"):
        for d in search_dirs:
            candidate = d / data_path.name
            if candidate.exists():
                logger.info("从数据集配置目录加载: %s", candidate)
                return candidate.resolve()

    by_name = dataset_yaml_path(data_path.stem)
    if by_name.exists():
        logger.info("通过 dataset_yaml_path 解析: %s", by_name)
        return by_name

    logger.warning(
        "数据集 YAML 未找到: %s（已尝试 %s 与 dataset_yaml_path）",
        data_path.name,
        DATASET_CONFIGS_DIR,
    )
    return data_path
