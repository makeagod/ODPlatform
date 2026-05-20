# -*- coding: utf-8 -*-
"""
数据流水线包暴露层
"""
from odp_platform.data_pipeline.orchestrator import DataPipelineOrchestrator
from odp_platform.data_pipeline.registry import ConverterRegistry

# 💡 必须在此处引入具体格式驱动，隐式触发其顶部的 @ConverterRegistry.register 装饰器进行注册挂载
from odp_platform.data_pipeline.core import pascal_voc, coco, yolo


def get_pipeline_capabilities() -> dict:
    """提供给 CLI 的能力矩阵查询接口"""
    # 动态构建各个格式支持的任务矩阵
    formats = ConverterRegistry.get_supported_formats()
    return {fmt: ["object_detection"] for fmt in formats}


class ConvertOptions:
    """轻量级全局流水线配置块"""
    def __init__(self, random_state: int = 42):
        self.random_state = random_state