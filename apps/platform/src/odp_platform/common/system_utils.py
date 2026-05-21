# -*- coding: utf-8 -*-
"""会话级环境信息日志。"""
from __future__ import annotations

import logging
import platform


def log_device_info(logger: logging.Logger) -> None:
    """在 validate 等端到端入口调用一次。"""
    logger.info(
        "运行环境: %s %s | Python %s",
        platform.system(),
        platform.release(),
        platform.python_version(),
    )
    try:
        import torch

        cuda = torch.cuda.is_available()
        device = torch.cuda.get_device_name(0) if cuda else "N/A"
        logger.info("PyTorch %s | CUDA: %s | GPU: %s", torch.__version__, cuda, device)
    except ImportError:
        logger.info("PyTorch: 未安装（仅做数据质检时可忽略）")
