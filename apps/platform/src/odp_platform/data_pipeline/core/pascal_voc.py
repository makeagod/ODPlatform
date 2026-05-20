# -*- coding: utf-8 -*-
"""
阶段 2: Pascal VOC 格式解析转换器
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List
from odp_platform.data_pipeline.registry import ConvertOptions


class PascalVocConverter:
    """Pascal VOC 格式数据集解析器"""

    def __init__(self, options: ConvertOptions = None):
        # 如果没有传入配置项，则使用默认配置
        self.options = options or ConvertOptions()

    def parse_annotation(self, xml_path: Path) -> Dict[str, Any]:
        """
        解析单个 VOC XML 标注文件
        :param xml_path: XML 文件的绝对路径
        :return: 包含图像元数据和标准化标注特征的字典
        """
        if not xml_path.exists():
            raise FileNotFoundError(f"未找到标注文件: {xml_path}")

        # 使用 Python 自带的 ElementTree 解析 XML
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # 1. 基础图像元数据提取
        filename = root.find("filename").text
        size_node = root.find("size")
        width = int(size_node.find("width").text)
        height = int(size_node.find("height").text)

        # 2. 迭代解析所有目标物体 (object 标签)
        annotations = []
        for obj in root.findall("object"):
            class_name = obj.find("name").text

            # 类别过滤逻辑：如果在 ConvertOptions 里指定了类别白名单，不在名单内的直接无视
            if self.options.classes is not None and class_name not in self.options.classes:
                continue

            bndbox = obj.find("bndbox")
            xmin = float(bndbox.find("xmin").text)
            ymin = float(bndbox.find("ymin").text)
            xmax = float(bndbox.find("xmax").text)
            ymax = float(bndbox.find("ymax").text)

            # 将绝对坐标打包暂存
            annotations.append({
                "category": class_name,
                "bbox": [xmin, ymin, xmax, ymax]
            })

        return {
            "filename": filename,
            "width": width,
            "height": height,
            "annotations": annotations
        }

    def validate_dataset_integrity(self, raw_dir: Path) -> float:
        """
        校验本地 VOC 数据集的完整度（覆盖率）
        :param raw_dir: 包含原图与 XML 的根目录
        :return: 成功解析的 XML 占比 (0.0 ~ 1.0)
        """
        # 假设 VOC 标准结构中 XML 都在 Annotations 文件夹下
        xml_dir = raw_dir / "Annotations"
        if not xml_dir.exists():
            # 兼容非标准结构，直接在根目录下找 xml
            xml_dir = raw_dir

        xml_files = list(xml_dir.glob("*.xml"))
        if not xml_files:
            return 0.0

        valid_count = 0
        for xml_file in xml_files:
            try:
                # 尝试解析，如果没有抛出异常则视为有效
                self.parse_annotation(xml_file)
                valid_count += 1
            except Exception:
                continue

        return valid_count / len(xml_files)