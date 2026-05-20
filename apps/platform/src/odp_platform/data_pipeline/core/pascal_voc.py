# -*- coding: utf-8 -*-
"""
阶段 4: Pascal VOC 标注格式流式解析驱动
"""
import xml.etree.ElementTree as ET
from pathlib import Path

from odp_platform.data_pipeline.registry import ConverterRegistry


def _text(node) -> str | None:
    return node.text.strip() if node is not None and node.text else None


@ConverterRegistry.register("pascal_voc")
class PascalVocConverter:
    """负责解析 Pascal VOC 规范 XML 标注文件的专用驱动"""

    def parse_annotation(self, file_path: Path) -> dict:
        """
        解析单张 XML 标注文件，规整为平台统一的中间层元数据标准字典
        :param file_path: XML 文件的物理路径
        :return: 规范化的元数据 Dict
        """
        tree = ET.parse(file_path)
        root = tree.getroot()

        filename_node = root.find("filename")
        filename = _text(filename_node) or f"{file_path.stem}.jpg"

        size_node = root.find("size")
        if size_node is None:
            raise ValueError(f"XML 缺少 <size> 节点: {file_path}")

        width = int(_text(size_node.find("width")) or 0)
        height = int(_text(size_node.find("height")) or 0)
        if width <= 0 or height <= 0:
            raise ValueError(f"XML <size> 无效 (width={width}, height={height}): {file_path}")

        annotations = []
        for obj in root.findall("object"):
            name_node = obj.find("name")
            category = _text(name_node)
            if not category:
                continue

            bndbox = obj.find("bndbox")
            if bndbox is None:
                continue

            xmin = float(_text(bndbox.find("xmin")) or 0)
            ymin = float(_text(bndbox.find("ymin")) or 0)
            xmax = float(_text(bndbox.find("xmax")) or 0)
            ymax = float(_text(bndbox.find("ymax")) or 0)

            annotations.append({
                "category": category,
                "bbox": [xmin, ymin, xmax, ymax],
            })

        return {
            "filename": filename,
            "width": width,
            "height": height,
            "annotations": annotations,
        }
