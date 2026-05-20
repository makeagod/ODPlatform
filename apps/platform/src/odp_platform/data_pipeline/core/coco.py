# -*- coding: utf-8 -*-
"""
阶段 4: COCO 标注格式流式解析驱动 (标准骨架)
"""
import json
from pathlib import Path
from odp_platform.data_pipeline.registry import ConverterRegistry


@ConverterRegistry.register("coco")
class CocoConverter:
    """负责解析 COCO 规范 JSON 标注文件的专用驱动"""

    def parse_annotation(self, file_path: Path) -> dict:
        """
        解析单张 COCO JSON 标注文件 (流式骨架，由于 COCO 是一整个巨型 JSON，后续进阶会配合 tempfile 优化)
        :param file_path: COCO JSON 文件的物理路径
        :return: 规范化的中间层字典结构
        """
        # 这里预留标准接口骨架，大总管调用时能保持完全一致的接口等价性
        return {
            "filename": "",
            "width": 0,
            "height": 0,
            "annotations": []
        }