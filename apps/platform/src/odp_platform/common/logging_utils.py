# -*- coding: utf-8 -*-
"""
兼容层：日志实现已迁移至 ``odp_platform.logging``。

新代码请使用::

    from odp_platform.logging import setup_cli_logging, get_logger
"""
from odp_platform.logging import ROOT_LOGGER_NAME, get_logger

__all__ = ["ROOT_LOGGER_NAME", "get_logger"]
