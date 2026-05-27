# -*- coding: utf-8 -*-
"""评估完成后归档 val JSON 结果到 CHECKPOINTS_DIR 旁的评估产物目录。"""
from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from odp_platform.common.paths import MODELS_DIR

logger = logging.getLogger(__name__)

EVAL_ARCHIVE_DIR: Path = MODELS_DIR / "evaluations"


def archive_val_results(
    val_dir: Path,
    model_filename: str | Path,
    *,
    archive_dir: Path | None = None,
) -> dict[str, Path | None]:
    """将 val 产出的 results JSON / 图表归档到 models/evaluations/."""
    archive_dir = archive_dir or EVAL_ARCHIVE_DIR
    results: dict[str, Path | None] = {"metrics_json": None, "confusion_matrix": None}

    if not val_dir.is_dir():
        logger.warning("评估目录不存在或不是目录，跳过归档: %s", val_dir)
        return results

    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.warning("创建归档目录失败，跳过归档: %s", e)
        return results

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_model_name = Path(model_filename).stem
    val_suffix = val_dir.name

    for src_name, label in [
        ("coco_metrics.json", "metrics_json"),
        ("confusion_matrix.png", "confusion_matrix"),
    ]:
        src_path = val_dir / src_name
        if not src_path.exists():
            continue

        dest_name = f"{val_suffix}-{timestamp}-{base_model_name}-{src_name}"
        dest_path = archive_dir / dest_name

        try:
            shutil.copy2(src_path, dest_path)
            logger.info("评估产物已归档: %s", dest_path.name)
            results[label] = dest_path
        except (OSError, shutil.Error) as e:
            logger.warning("归档 %s 失败: %s", src_name, e)

    return results
