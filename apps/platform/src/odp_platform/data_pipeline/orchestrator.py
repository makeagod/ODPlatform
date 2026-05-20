# -*- coding: utf-8 -*-
"""
阶段 8: 端到端数据流水线编排核心大总管 (包含 Fail-Fast 覆盖率检查与完整闭环)
"""
from pathlib import Path
from typing import List, Dict, Any, Optional

from odp_platform.common import paths
from odp_platform.data_pipeline.registry import get_converter, ConvertOptions
from odp_platform.data_pipeline.split.manifest import DatasetManifest, SampleItem
from odp_platform.data_pipeline.split.materializer import DatasetMaterializer
from odp_platform.data_pipeline.split.yaml_writer import YoloYamlWriter
from odp_platform.data_pipeline.split.splitter import DatasetSplitter

# 工业界标准：原始数据集至少要有 50% 的样本能够被成功解析，否则触发熔断，防止脏数据污染训练
MIN_DATASET_COVERAGE = 0.5


class DataPipelineOrchestrator:
    """端到端管理数据提取、Fail-Fast 检查、切分以及标准 YOLO 格式落盘的编排大总管"""

    def __init__(self, dataset_name: str, raw_format: str, options: Optional[ConvertOptions] = None):
        self.dataset_name = dataset_name
        self.raw_format = raw_format
        self.options = options or ConvertOptions()

        # 🚀 思考题 7：为什么将 _user_classes 和 _final_classes 属性分开？
        # _user_classes 记录用户在前端/配置里显式想要过滤的类别
        self._user_classes: Optional[List[str]] = self.options.classes
        # _final_classes 记录最终在数据集中实际扫描、汇总出来的确切类别列表（用于生成 yaml 的 names 映射）
        self._final_classes: List[str] = []

        # 获取对应的具体格式转换器实例
        converter_cls = get_converter(raw_format)
        self.converter = converter_cls(self.options)

    def _check_raw_dataset_coverage(self, raw_dir: Path):
        """
        🚀 思考题 8：Fail-Fast 机制。
        在转换前检查数据集覆盖率，如果低于 50% 立刻抛错终止，防止浪费算力去处理残缺数据集。
        """
        coverage = self.converter.validate_dataset_integrity(raw_dir)
        if coverage < MIN_DATASET_COVERAGE:
            raise ValueError(
                f"【Fail-Fast 熔断】数据集 '{self.dataset_name}' 的合规覆盖率仅为 {coverage * 100:.1%}, "
                f"低于系统要求的最低阈值 {MIN_DATASET_COVERAGE * 100:.0%}%! "
                f"请检查原始数据包是否残缺或格式不符。"
            )

    def run_pipeline(
            self,
            train_ratio: float = 0.7,
            val_ratio: float = 0.2,
            test_ratio: float = 0.1
    ) -> Path:
        """
        执行端到端全自动流水线
        :return: 生成的 YAML 训练配置文件路径
        """
        # 1. 定位原始输入目录 (如 data/raw/X)
        raw_dataset_dir = paths.RAW_DATA_DIR / self.dataset_name
        if not raw_dataset_dir.exists():
            raise FileNotFoundError(f"未在指定位置找到原始数据集目录: {raw_dataset_dir}")

        # 2. 执行核心的 Fail-Fast 覆盖率安全检查
        self._check_raw_dataset_coverage(raw_dataset_dir)

        # 3. 扫描并组装标准清单 DatasetManifest
        # 这里以经典的 Pascal VOC 结构为例进行流式组装
        manifest = DatasetManifest()
        xml_dir = raw_dataset_dir / "Annotations"
        if not xml_dir.exists():
            xml_dir = raw_dataset_dir

        img_dir = raw_dataset_dir / "JPEGImages"
        if not img_dir.exists():
            img_dir = raw_dataset_dir

        detected_classes = set()
        for xml_file in xml_dir.glob("*.xml"):
            try:
                # 借助对应的具体转换器解析出标准中间态结构
                parsed_meta = self.converter.parse_annotation(xml_file)

                # 寻找对应的原图路径（尝试常见后缀）
                img_name = parsed_meta["filename"]
                img_path = img_dir / img_name
                if not img_path.exists():
                    # 容错：如果 xml 里记的图片名字找不到，尝试直接用 xml 同名找图片
                    for ext in [".jpg", ".jpeg", ".png", ".JPG"]:
                        alt_path = img_dir / (xml_file.stem + ext)
                        if alt_path.exists():
                            img_path = alt_path
                            break

                if not img_path.exists():
                    continue

                # 收集遇到的所有类别名称
                for ann in parsed_meta["annotations"]:
                    detected_classes.add(ann["category"])

                # 构建清单条目并塞进大容器
                item = SampleItem(
                    image_path=img_path,
                    annotations=parsed_meta["annotations"],
                    width=parsed_meta["width"],
                    height=parsed_meta["height"],
                    raw_format=self.raw_format
                )
                manifest.add_item(item)
            except Exception:
                continue

        if manifest.size == 0:
            raise RuntimeError(f"数据集中未扫描到任何有效的图片及对应的标注样本！")

        # 4. 动态确立最终的类别列表，并生成严密的 index 映射字典
        self._final_classes = sorted(list(detected_classes))
        class_to_idx = {name: idx for idx, name in enumerate(self._final_classes)}

        # 5. 调用智能切分器进行切分计算
        splitter = DatasetSplitter(
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            random_state=self.options.random_state
        )
        train_items, val_items, test_items = splitter.split(manifest)

        # 6. 使用依赖注入的落地器执行物理拷贝与 YOLO 转产
        processed_dataset_root = paths.PROCESSED_DATA_DIR / self.dataset_name
        materializer = DatasetMaterializer(processed_dataset_root)

        train_count = materializer.materialize_split("train", train_items, class_to_idx)
        val_count = materializer.materialize_split("val", val_items, class_to_idx)
        test_count = materializer.materialize_split("test", test_items, class_to_idx)

        # 7. 整理元数据，交由 YAML 生成器写出配置文件
        metadata = {
            "random_state": self.options.random_state,
            "split_counts": {
                "train": train_count,
                "val": val_count,
                "test": test_count,
                "total_input": manifest.size
            }
        }
        yaml_writer = YoloYamlWriter(paths.DATASET_CONFIGS_DIR)
        config_yaml_path = yaml_writer.write_dataset_config(
            dataset_name=self.dataset_name,
            processed_root_dir=processed_dataset_root,
            classes=self._final_classes,
            metadata=metadata
        )

        return config_yaml_path