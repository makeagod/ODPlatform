# -*- coding: utf-8 -*-
"""CLI 入口常用的日志装配封装。"""
from __future__ import annotations

import logging
from typing import Optional

from odp_platform.common.paths import LOGGING_DIR, META_LOGGING_DIR
from odp_platform.logging.constants import ROOT_LOGGER_NAME
from odp_platform.logging.setup import get_logger


def setup_cli_logging(
    log_type: str,
    *,
    log_level: int = logging.INFO,
    model_name: Optional[str] = None,
    temp_log: bool = False,
) -> logging.Logger:
    """为 platform CLI 装配日志（写入 ``apps/platform/logs/<log_type>/``）。"""
    return get_logger(
        base_path=LOGGING_DIR,
        log_type=log_type,
        model_name=model_name,
        log_level=log_level,
        temp_log=temp_log,
        logger_name=ROOT_LOGGER_NAME,
    )


def setup_audit_logging(
    log_type: str,
    *,
    log_level: int = logging.INFO,
    temp_log: bool = False,
) -> logging.Logger:
    """为元工具（如 odp-reset）装配审计日志（``apps/platform/.odp-meta/logs/``）。"""
    return get_logger(
        base_path=META_LOGGING_DIR,
        log_type=log_type,
        log_level=log_level,
        temp_log=temp_log,
        logger_name=ROOT_LOGGER_NAME,
    )
