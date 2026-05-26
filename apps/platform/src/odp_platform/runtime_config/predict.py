# -*- coding: utf-8 -*-
"""predict 任务配置（与 infer 同实现）。"""
from odp_platform.runtime_config.infer import YOLOInferConfig

YOLOPredictConfig = YOLOInferConfig

__all__ = ["YOLOInferConfig", "YOLOPredictConfig"]
