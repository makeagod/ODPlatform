# -*- coding: utf-8 -*-
"""
日志装配：为命名 logger 挂载彩色控制台 + 文件 handler。

业务模块只需 ``logging.getLogger(__name__)``；CLI 入口调用一次 ``get_logger`` / ``setup_cli_logging``。
"""
from __future__ import annotations

import logging
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from colorlog import ColoredFormatter

from odp_platform.logging.constants import ROOT_LOGGER_NAME


def _safe_model_segment(model_name: str) -> str:
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in model_name)


def _build_log_file(
    log_dir: Path,
    log_type: str,
    *,
    temp_log: bool,
    model_name: Optional[str],
) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:21]
    prefix = "temp" if temp_log else log_type.replace("_", "-")
    parts = [prefix, timestamp]
    if model_name:
        parts.append(_safe_model_segment(model_name))
    return log_dir / ("_".join(parts) + ".log")


def get_logger(
    base_path: Path,
    log_type: str = "general",
    model_name: Optional[str] = None,
    log_level: int = logging.INFO,
    temp_log: bool = False,
    encoding: str = "utf-8",
    logger_name: str = ROOT_LOGGER_NAME,
) -> logging.Logger:
    """
    配置命名 logger（默认 ``odp_platform``），挂载 console + file handler。

    幂等：同一 ``logger_name`` 已配置 handler 时直接返回，避免重复输出。
    """
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    logger.setLevel(log_level)
    logger.propagate = False

    log_file = _build_log_file(
        Path(base_path) / log_type,
        log_type,
        temp_log=temp_log,
        model_name=model_name,
    )

    file_formatter = logging.Formatter(
        fmt=(
            "%(asctime)s - %(name)s - %(levelname)-8s - "
            "%(filename)s:%(lineno)d - %(funcName)s - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(log_file, encoding=encoding)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    console_formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s%(reset)s "
        "%(log_color)s[%(levelname)-8s]%(reset)s "
        "%(cyan)s%(filename)-25s%(reset)s:"
        "%(blue)s%(lineno)-4d%(reset)s "
        "%(log_color)s│ %(message)s%(reset)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "white",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red,bg_white",
        },
        style="%",
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("=" * 60)
    logger.info("日志系统初始化完成")
    logger.info("运行环境: %s %s", platform.system(), platform.release())
    logger.info("阶段类型: %s", log_type)
    logger.info("日志文件: %s", log_file)
    logger.info("日志级别: %s", logging.getLevelName(log_level))
    logger.info("模型名称: %s", model_name or "无")
    logger.info("=" * 60)

    return logger
