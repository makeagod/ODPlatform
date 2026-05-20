# -*- coding: utf-8 -*-
"""
阶段 1: 数据流水线业务调度层
"""
from typing import Dict, Tuple
from odp_platform.data_pipeline.registry import list_capabilities, get_converter, ConvertOptions


def get_pipeline_capabilities() -> Dict[str, Tuple[str, ...]]:
    """
    获取当前系统支持的数据处理能力矩阵（供 CLI 实时打印帮助文档）
    """
    return list_capabilities()


def validate_format_support(format_name: str, task: str = "detect") -> bool:
    """
    校验某个格式是否支持特定的计算机视觉任务
    """
    capabilities = get_pipeline_capabilities()
    if format_name not in capabilities:
        return False
    return task in capabilities[format_name]