# -*- coding: utf-8 -*-
"""
阶段 1: 转换器注册表与配置项定义
"""
import dataclasses
from typing import Dict, List, Optional, Tuple, Type, Callable


@dataclasses.dataclass
class ConvertOptions:
    """数据转换与过滤的基础配置项"""
    # 目标提取的类别列表。None 表示提取数据集中所有可见类别，[] 表示不提取任何类别
    classes: Optional[List[str]] = None
    # 转换过程中的随机种子，确保划分数据集时可复现
    random_state: int = 42


# 全局注册表容器，结构为: { 格式名称: (转换器类, 支持的任务元组) }
_CONVERTER_REGISTRY: Dict[str, Tuple[Type, Tuple[str, ...]]] = {}
_is_initialized = False


def _lazy_init():
    """
    延迟加载机制：只有当真正调用注册表查询时，才动态 import 具体的转换器实现。
    🔥 注意：由于此时 core/ 目录下的具体实现还没写，阶段 1~3 期间严禁在外部触发此函数！
    """
    global _is_initialized
    if _is_initialized:
        return

    try:
        # 动态导入各个具体的转换器类
        from odp_platform.data_pipeline.core.pascal_voc import PascalVocConverter
        from odp_platform.data_pipeline.core.coco import CocoConverter
        from odp_platform.data_pipeline.core.yolo import YoloConverter
        from odp_platform.common import constants

        # 将它们注册到全局字典中
        _CONVERTER_REGISTRY[constants.PASCAL_VOC] = (PascalVocConverter, (constants.TASK_DETECT,))
        _CONVERTER_REGISTRY[constants.COCO] = (CocoConverter, (constants.TASK_DETECT, constants.TASK_SEGMENT))
        _CONVERTER_REGISTRY[constants.YOLO] = (YoloConverter, (constants.TASK_DETECT,))

        _is_initialized = True
    except ImportError as e:
        # 阶段 1~3 期间如果误触发，会因为找不到 core 模块而抛出该异常
        raise RuntimeError(
            f"注册表初始化失败，可能由于依赖的 Converter 尚未实现。错误详情: {e}"
        ) from e


def list_capabilities() -> Dict[str, Tuple[str, ...]]:
    """
    对外公共 API：获取当前平台支持的所有格式及其能力矩阵
    :return: 例如 {'pascal_voc': ('detect',), 'coco': ('detect', 'segment')}
    """
    _lazy_init()
    return {format_name: info[1] for format_name, info in _CONVERTER_REGISTRY.items()}


def get_converter(format_name: str) -> Type:
    """
    对外公共 API：根据格式名称获取对应的转换器类
    """
    _lazy_init()
    if format_name not in _CONVERTER_REGISTRY:
        raise ValueError(f"暂不支持的数据集格式: '{format_name}'，当前已支持: {list(list_capabilities().keys())}")
    return _CONVERTER_REGISTRY[format_name][0]