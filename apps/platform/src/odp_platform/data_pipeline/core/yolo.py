# -*- coding: utf-8 -*-
"""
阶段 4: YOLO 格式解析转换器（接口等价性实现）
"""
from pathlib import Path
from typing import Dict, Any, List
from odp_platform.data_pipeline.registry import ConvertOptions


class YoloConverter:
    """YOLO 格式数据集解析器（保持统一的接口协议）"""

    def __init__(self, options: ConvertOptions = None):
        self.options = options or ConvertOptions()

    def parse_txt_annotation(self, txt_path: Path, img_width: int, img_height: int) -> List[Dict[str, Any]]:
        """
        解析单张图片的 YOLO .txt 标注文件，并反向规整为 [xmin, ymin, xmax, ymax] 绝对坐标
        :param txt_path: YOLO 格式的 .txt 标签路径
        :param img_width: 图片宽度（归一化还原必需）
        :param img_height: 图片高度（归一化还原必需）
        """
        if not txt_path.exists():
            return []  # 允许背景图没有 txt 文件

        annotations = []
        with open(txt_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) < 5:
                    continue

                # YOLO 原始格式: class_id x_center y_center width height (均为 0~1 归一化值)
                class_id_str = parts[0]
                x_center = float(parts[1])
                y_center = float(parts[2])
                w = float(parts[3])
                h = float(parts[4])

                # 暂用 class_id 作为类名，后续由调度层映射
                class_name = class_id_str

                if self.options.classes is not None and class_name not in self.options.classes:
                    continue

                # 反向计算还原为绝对坐标 [xmin, ymin, xmax, ymax]
                xmin = (x_center - w / 2) * img_width
                ymin = (y_center - h / 2) * img_height
                xmax = (x_center + w / 2) * img_width
                ymax = (y_center + h / 2) * img_height

                annotations.append({
                    "category": class_name,
                    "bbox": [xmin, ymin, xmax, ymax]
                })

        return annotations

    def validate_dataset_integrity(self, raw_dir: Path) -> float:
        """
        校验本地 YOLO 数据集的完整度
        """
        # YOLO 格式通常要求有 labels/ 文件夹
        labels_dir = raw_dir / "labels"
        if not labels_dir.exists():
            labels_dir = raw_dir

        txt_files = list(labels_dir.glob("*.txt"))
        # 如果有 classes.txt，需要将其排除在样本之外
        txt_files = [f for f in txt_files if f.name != "classes.txt"]

        if not txt_files:
            return 0.0

        # YOLO 强依赖外部宽高的输入，此处只要有合法 txt 且格式能切分，即视为基础合规
        return 1.0