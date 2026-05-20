# -*- coding: utf-8 -*-
"""
D3 数据准备子系统暴露给外部的统一接口网关
"""

from odp_platform.data_pipeline.registry import ConvertOptions
from odp_platform.data_pipeline.service import (
    get_pipeline_capabilities,
    validate_format_support,
)

# 显式声明暴露的公共 API，防止老代码被意外破坏
__all__ = [
    "ConvertOptions",
    "get_pipeline_capabilities",
    "validate_format_support",
]