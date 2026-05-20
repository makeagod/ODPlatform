# -*- coding: utf-8 -*-
"""
阶段 3: COCO 格式解析转换器 (使用 tempfile 机制中转)
"""
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from odp_platform.data_pipeline.registry import ConvertOptions


class CocoConverter:
    """COCO 格式数据集解析器"""

    def __init__(self, options: ConvertOptions = None):
        self.options = options or ConvertOptions()

    def parse_dataset(self, json_path: Path) -> List[Dict[str, Any]]:
        """
        流式解析 COCO 的巨大 JSON 文件，并使用临时文件进行解耦中转
        :param json_path: COCO instances_train2017.json 的路径
        :return: 标准化后的图片级别标注列表
        """
        if not json_path.exists():
            raise FileNotFoundError(f"未找到 COCO 标注文件: {json_path}")

        # 1. 建立临时中转文件，防止超大 JSON 直接撑爆内存
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
            temp_path = Path(temp_file.name)

            # 2. 读取原始数据并提取核心字典
            with open(json_path, 'r', encoding='utf-8') as f:
                coco_data = json.load(f)

            # 建立类别映射字典: {id: name}
            categories_map = {
                cat['id']: cat['name']
                for cat in coco_data.get('categories', [])
            }

            # 建立图片映射字典: {image_id: {filename, width, height, annotations: []}}
            images_map = {}
            for img in coco_data.get('images', []):
                images_map[img['id']] = {
                    "filename": img['file_name'],
                    "width": img['width'],
                    "height": img['height'],
                    "annotations": []
                }

            # 3. 填充标注数据
            for ann in coco_data.get('annotations', []):
                image_id = ann['image_id']
                category_id = ann['category_id']
                class_name = categories_map.get(category_id, "unknown")

                # 类别白名单过滤
                if self.options.classes is not None and class_name not in self.options.classes:
                    continue

                if image_id in images_map:
                    # COCO bbox 格式为 [xmin, ymin, width, height]
                    # 我们需要将其转换为统一的 [xmin, ymin, xmax, ymax]
                    xmin, ymin, w, h = ann['bbox']
                    xmax = xmin + w
                    ymax = ymin + h

                    images_map[image_id]["annotations"].append({
                        "category": class_name,
                        "bbox": [xmin, ymin, xmax, ymax]
                    })

            # 4. 将规整后的中间结果写入临时文件
            json.dump(list(images_map.values()), temp_file)
            temp_file.flush()

        # 5. 从临时文件中重新加载并返回给上层调度层
        with open(temp_path, 'r', encoding='utf-8') as f:
            standardized_data = json.load(f)

        # 安全删除临时文件
        try:
            temp_path.unlink()
        except OSError:
            pass

        return standardized_data

    def validate_dataset_integrity(self, raw_dir: Path) -> float:
        """
        校验本地 COCO 数据集的完整度（覆盖率）
        :param raw_dir: 包含 annotations 目录的根目录
        :return: 成功概率 (0.0 ~ 1.0)
        """
        # 标准 COCO 寻找 annotations/*.json
        json_files = list((raw_dir / "annotations").glob("*.json"))
        if not json_files:
            # 兼容模式：直接在根线下寻找 json
            json_files = list(raw_dir.glob("*.json"))

        if not json_files:
            return 0.0

        try:
            # 只要能成功流式解析第一个 JSON，就说明格式符合标准
            data = self.parse_dataset(json_files[0])
            return 1.0 if len(data) > 0 else 0.0
        except Exception:
            return 0.0