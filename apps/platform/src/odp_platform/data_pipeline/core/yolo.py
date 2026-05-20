# -*- coding: utf-8 -*-
"""
阶段 4: YOLO 标注格式流式解析驱动 (标准骨架)
"""
from pathlib import Path
from odp_platform.data_pipeline.registry import ConverterRegistry


@ConverterRegistry.register("yolo")
class YoloConverter:
    """负责解析 YOLO 文本标注文件的专用驱动"""

    def parse_annotation(self, file_path: Path) -> dict:
        """
        解析单张 YOLO .txt 标注文件 (保持接口等价性)
        :param file_path: YOLO 文本文件的物理路径
        :return: 规范化的中间层字典结构
        """
        return {
            "filename": "",
            "width": 0,
            "height": 0,
            "annotations": []
        }