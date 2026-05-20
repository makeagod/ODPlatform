# -*- coding: utf-8 -*-
"""
阶段 7: Ultralytics 标准训练 YAML 生成器 (集成 odp_meta 元数据追踪)
"""
import datetime
import yaml
from pathlib import Path
# 💡 【修复】显式导入 Any 避免 NameError
from typing import List, Dict, Any


class YoloYamlWriter:
    """负责将数据集的类别结构与划分结果持久化为 YOLO 训练 YAML 文件的生成器"""

    def __init__(self, config_dir: Path):
        """
        :param config_dir: YAML 文件的统一存放路径 (对应 paths.DATASET_CONFIGS_DIR)
        """
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def write_dataset_config(
        self,
        dataset_name: str,
        processed_root_dir: Path,
        classes: List[str],
        metadata: Dict[str, Any]
    ) -> Path:
        """
        生成完整的训练 YAML 配置文件
        :param dataset_name: 数据集名称
        :param processed_root_dir: 转换落地后的 data/processed/<dataset_name> 绝对路径
        :param classes: 规整后的类别名称列表（其索引即为 YOLO 标签 ID）
        :param metadata: 用于审计追踪的元数据块
        :return: 生成的 YAML 文件路径
        """
        yaml_path = self.config_dir / f"{dataset_name}.yaml"

        # 构建标准的 Ultralytics YAML 字典结构
        yaml_data = {
            # 1. 根目录与子集路径定义 (支持相对路径或绝对路径)
            "path": str(processed_root_dir.resolve()),
            "train": "train/images",
            "val": "val/images",
            "test": "test/images",

            # 2. 类别数量与映射 (Ultralytics 标准字段)
            "nc": len(classes),
            "names": {idx: name for idx, name in enumerate(classes)},

            # 3. ⚠️ 注入 ODP 专属的高级元数据审计块，用于数据回溯与规范性检查
            "schema_version": 1,
            "odp_meta": {
                "dataset_name": dataset_name,
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "random_state": metadata.get("random_state", 42),
                "split_counts": metadata.get("split_counts", {})
            }
        }

        # 写入物理磁盘，确保中文字符不变成 unicode 编码
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                yaml_data,
                f,
                allow_unicode=True,
                sort_keys=False,
                indent=4
            )

        return yaml_path