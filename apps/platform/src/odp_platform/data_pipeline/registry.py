# -*- coding: utf-8 -*-
"""
阶段 4: 转换驱动延迟加载注册表 (解耦上游格式驱动)
"""
import logging
# 💡 【核心修复】显式导入 Any 避免 NameError
from typing import Dict, Type, List, Any

logger = logging.getLogger("odp-platform")


class ConverterRegistry:
    """
    统一格式驱动注册表 (Registry 模式)
    负责解耦和动态路由：上游格式解析驱动注册到此，大总管根据入参一键调取。
    """
    _registry: Dict[str, Type] = {}

    @classmethod
    def register(cls, raw_format: str):
        """
        类装饰器：用于在各个具体驱动（如 pascal_voc.py）顶部动态注册驱动
        :param raw_format: 注册的格式名称小写 (例如 'pascal_voc', 'coco')
        """

        def decorator(sub_cls):
            cls._registry[raw_format.lower()] = sub_cls
            return sub_cls

        return decorator

    @classmethod
    def get_converter(cls, raw_format: str) -> Any:
        """
        网关路由方法：根据传入格式，动态实例化并返回对应的转换驱动
        :param raw_format: 格式名称 (如 'pascal_voc')
        """
        fmt_key = raw_format.lower()
        if fmt_key not in cls._registry:
            raise ValueError(
                f"❌ 平台暂不支持的源数据格式: '{raw_format}'。"
                f"当前已激活注册的能力矩阵为: {list(cls._registry.keys())}"
            )

        # 延迟加载实例化驱动
        converter_cls = cls._registry[fmt_key]
        return converter_cls()

    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """获取当前系统已成功挂载的所有格式列表"""
        return list(cls._registry.keys())