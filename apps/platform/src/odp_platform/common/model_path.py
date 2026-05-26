# -*- coding: utf-8 -*-
"""解析预训练 / checkpoint 路径。"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from odp_platform.common.paths import CHECKPOINTS_DIR, PRETRAINED_MODELS_DIR

logger = logging.getLogger(__name__)

_DEFAULT_SEARCH_DIRS = (PRETRAINED_MODELS_DIR, CHECKPOINTS_DIR)


def resolve_model_path(
    model: str | Path,
    search_dirs: Sequence[Path] | None = None,
) -> Path:
    model_path = Path(model)

    if model_path.is_absolute():
        return model_path.resolve()

    dirs = search_dirs if search_dirs is not None else _DEFAULT_SEARCH_DIRS
    for d in dirs:
        candidate = d / model_path.name
        if candidate.exists():
            logger.info("模型已定位: %s (来自 %s)", candidate, d)
            return candidate.resolve()

    logger.warning(
        "模型文件未在搜索目录中找到: %s\n"
        "已搜索: %s\n"
        "可传入绝对路径，或将权重放入 %s",
        model_path.name,
        [str(d) for d in dirs],
        PRETRAINED_MODELS_DIR,
    )
    return model_path
