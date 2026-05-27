# -*- coding: utf-8 -*-
"""D8 模型推理子系统公共 API。"""
from __future__ import annotations

from odp_platform.inference.service import InferResult, InferService, predict_yolo

__all__ = [
    "InferService",
    "InferResult",
    "predict_yolo",
]
