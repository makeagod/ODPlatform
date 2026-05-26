# -*- coding: utf-8 -*-
"""训练完成后归档 best/last.pt 到 CHECKPOINTS_DIR。"""
from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

from odp_platform.common.paths import CHECKPOINTS_DIR

logger = logging.getLogger(__name__)


def archive_checkpoints(
    train_dir: Path,
    model_filename: str | Path,
    *,
    checkpoint_dir: Path | None = None,
) -> dict[str, Path]:
    checkpoint_dir = checkpoint_dir or CHECKPOINTS_DIR
    results: dict[str, Path] = {}

    if not train_dir.is_dir():
        logger.warning("训练目录不存在或不是目录，跳过归档: %s", train_dir)
        return results

    try:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.warning("创建归档目录失败，跳过归档: %s", e)
        return results

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_model_name = Path(model_filename).stem
    train_suffix = train_dir.name

    for model_type in ("best", "last"):
        src_path = train_dir / "weights" / f"{model_type}.pt"
        if not src_path.exists():
            logger.warning("未找到权重文件，跳过: %s", src_path)
            continue

        dest_name = f"{train_suffix}-{timestamp}-{base_model_name}-{model_type}.pt"
        dest_path = checkpoint_dir / dest_name

        try:
            shutil.copy2(src_path, dest_path)
            logger.info("权重已归档: %s", dest_path.name)
            results[model_type] = dest_path
        except (OSError, shutil.Error) as e:
            logger.warning("归档 %s.pt 失败: %s", model_type, e)

    return results
