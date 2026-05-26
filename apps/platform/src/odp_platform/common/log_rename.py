# -*- coding: utf-8 -*-
"""训练结束后将日志文件名与 ultralytics save_dir 对齐。"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from odp_platform.logging.constants import ROOT_LOGGER_NAME

logger = logging.getLogger(__name__)

_TIMESTAMP_RE = re.compile(r"(\d{8}-\d{6}(?:-\d+)?)")


def rename_log_to_save_dir(
    save_dir: Path,
    model_stem: str,
) -> Path | None:
    root = logging.getLogger(ROOT_LOGGER_NAME)

    file_handler = next(
        (h for h in root.handlers if isinstance(h, logging.FileHandler)),
        None,
    )
    if file_handler is None:
        logger.warning(
            "'%s' 根 logger 上没有 FileHandler，跳过日志改名",
            ROOT_LOGGER_NAME,
        )
        return None

    old_path = Path(file_handler.baseFilename)

    match = _TIMESTAMP_RE.search(old_path.stem)
    timestamp = match.group(1) if match else "unknown-time"
    if not match:
        logger.warning("原日志文件名缺时间戳，用占位符: %s", old_path.name)

    new_name = f"{save_dir.name}_{timestamp}_{model_stem}.log"
    new_path = old_path.parent / new_name

    if new_path == old_path:
        return old_path

    formatter = file_handler.formatter
    level = file_handler.level
    encoding = getattr(file_handler, "encoding", None) or "utf-8"

    file_handler.close()
    root.removeHandler(file_handler)

    if not old_path.exists():
        logger.warning("旧日志文件不存在，无法改名: %s", old_path)
        return None

    try:
        old_path.rename(new_path)
    except OSError as e:
        logger.warning("日志 rename 失败 (%s)，尝试恢复旧 handler...", e)
        try:
            restored = logging.FileHandler(old_path, encoding=encoding)
            if formatter:
                restored.setFormatter(formatter)
            restored.setLevel(level)
            root.addHandler(restored)
        except OSError as e2:
            logger.error("回滚 handler 也失败 (%s)", e2)
        return None

    try:
        new_handler = logging.FileHandler(new_path, encoding=encoding)
        if formatter:
            new_handler.setFormatter(formatter)
        new_handler.setLevel(level)
        root.addHandler(new_handler)
    except OSError as e:
        logger.error("创建新 FileHandler 失败 (%s)", e)
        return new_path

    logger.info("日志文件已重命名: %s", new_path.name)
    return new_path
