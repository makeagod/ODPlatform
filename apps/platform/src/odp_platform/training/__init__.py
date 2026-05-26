# -*- coding: utf-8 -*-
"""D6 训练子系统公共 API。"""
from __future__ import annotations

from odp_platform.common.result import TrainMetrics
from odp_platform.training.service import TrainResult, TrainService, train_yolo

__all__ = [
    "TrainService",
    "TrainMetrics",
    "TrainResult",
    "train_yolo",
]
