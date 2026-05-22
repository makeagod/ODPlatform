# -*- coding: utf-8 -*-
"""ODPlatform 日志子系统（platform 端私有，目录位于 apps/platform）。"""
from odp_platform.logging.cli import setup_audit_logging, setup_cli_logging
from odp_platform.logging.constants import AUDIT_LOGGER_NAME, ROOT_LOGGER_NAME
from odp_platform.logging.setup import get_logger

__all__ = [
    "AUDIT_LOGGER_NAME",
    "ROOT_LOGGER_NAME",
    "get_logger",
    "setup_audit_logging",
    "setup_cli_logging",
]
