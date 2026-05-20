# -*- coding: utf-8 -*-
"""
阶段 6: 划分数据集的物理实体落地器 (使用依赖注入模式)
"""
import shutil
from pathlib import Path
from typing import List, Dict, Any
from odp_platform.data_pipeline.split.manifest import SampleItem


class DatasetMaterializer:
    """负责将内存中的样本数据拷贝并标准化写入本地磁盘的执行器"""

    def __init__(self, output_dir: Path):
        """
        通过构造函数注入目标落地根目录 (如 data/processed/dataset_name)
        """
        self.output_dir = output_dir

    def _convert_to_yolo_line(self, ann: Dict[str, Any], img_width: int, img_height: int, class_to_idx: Dict[str, int]) -> str:
        """将标准绝对坐标 bbox 转换为 YOLO 需要的归一化中心点宽高格式"""
        category = ann["category"]
        if category not in class_to_idx:
            return ""  # 忽略未映射的类别

        class_id = class_to_idx[category]
        xmin, ymin, xmax, ymax = ann["bbox"]

        # 计算绝对中心点和宽高
        box_w = xmax - xmin
        box_h = ymax - ymin
        x_center = xmin + box_w / 2.0
        y_center = ymin + box_h / 2.0

        # 归一化到 0 ~ 1 之间
        x_norm = x_center / img_width
        y_norm = y_center / img_height
        w_norm = box_w / img_width
        h_norm = box_h / img_height

        return f"{class_id} {x_norm:.6f} {y_norm:.6f} {w_norm:.6f} {h_norm:.6f}\n"

    def materialize_split(self, split_name: str, items: List[SampleItem], class_to_idx: Dict[str, int]) -> int:
        """
        将某一特定子集（train / val / test）物理写入磁盘
        :param split_name: "train", "val" 或 "test"
        :param items: 该子集分配到的 SampleItem 列表
        :param class_to_idx: 类别名称到 YOLO 整数 ID 的映射表
        :return: 成功落盘的样本总数
        """
        if not items:
            return 0

        # 1. 创建 YOLO 标准的物理目录树 (先清空旧文件, 避免重复运行后样本堆积)
        images_output_dir = self.output_dir / split_name / "images"
        labels_output_dir = self.output_dir / split_name / "labels"
        for out_dir in (images_output_dir, labels_output_dir):
            if out_dir.exists():
                for old_file in out_dir.iterdir():
                    if old_file.is_file():
                        old_file.unlink()
            out_dir.mkdir(parents=True, exist_ok=True)

        success_count = 0
        for item in items:
            src_image: Path = item.image_path
            if not src_image.exists():
                continue

            # 2. 安全拷贝原图到目标子集下
            dest_image = images_output_dir / src_image.name
            shutil.copy2(src_image, dest_image)

            # 3. 生成对应的 YOLO 格式 .txt 标签文件
            txt_name = src_image.stem + ".txt"
            dest_txt = labels_output_dir / txt_name

            yolo_lines = []
            for ann in item.annotations:
                line = self._convert_to_yolo_line(ann, item.width, item.height, class_to_idx)
                if line:
                    yolo_lines.append(line)

            # 写入文件（如果是背景图，也会生成空的 txt 文件，符合 YOLO 规范）
            with open(dest_txt, "w", encoding="utf-8") as f:
                f.writelines(yolo_lines)

            success_count += 1

        return success_count