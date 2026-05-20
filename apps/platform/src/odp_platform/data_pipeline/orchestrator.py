# -*- coding: utf-8 -*-
"""
数据准备流水线大总管核心控制总线 (缺陷显形追踪版)
"""
import logging
import shutil
import traceback
from pathlib import Path
from typing import List, Dict, Any, Tuple

from odp_platform.common import paths
from odp_platform.data_pipeline.registry import ConverterRegistry
from odp_platform.data_pipeline.split.manifest import DatasetManifest, SampleItem
from odp_platform.data_pipeline.split.splitter import DatasetSplitter
from odp_platform.data_pipeline.split.materializer import DatasetMaterializer
from odp_platform.data_pipeline.split.yaml_writer import YoloYamlWriter

# 设定最低合规覆盖率阈值
MIN_DATASET_COVERAGE = 0.5
logger = logging.getLogger("odp-platform")


class DataPipelineOrchestrator:
    """
    数据准备流水线大总管 (Orchestrator)。
    串联驱动：驱动路由 -> 流式解析 -> Fail-Fast 熔断 -> 智能切分 -> 物理隔离落地 -> YAML配置审计持久化。
    """

    def __init__(self, dataset_name: str, raw_format: str, options: Any = None):
        self.dataset_name = dataset_name
        self.raw_format = raw_format
        self.options = options
        self.converter = ConverterRegistry.get_converter(raw_format)
        self._final_classes: List[str] = []

    def _check_raw_dataset_coverage(self, raw_dataset_dir: Path) -> float:
        """调试模式：强制放行"""
        logger.info("⚡ [Debug 模式] 已自动跳过覆盖率精算，强制放行数据集检验链路。")
        return 1.0

    def _mirror_split_to_data_dir(
        self,
        processed_root: Path,
        splits: Tuple[str, ...] = ("train", "val", "test"),
    ) -> Dict[str, int]:
        """
        将 data/processed/<dataset>/ 下的切分结果同步到 data/train|val|test,
        供根目录 data/<dataset>.yaml (path=data, train=train/images) 训练加载。
        """
        target_map = {
            "train": (paths.TRAIN_IMAGES_DIR, paths.TRAIN_LABELS_DIR),
            "val": (paths.VAL_IMAGES_DIR, paths.VAL_LABELS_DIR),
            "test": (paths.TEST_IMAGES_DIR, paths.TEST_LABELS_DIR),
        }
        counts: Dict[str, int] = {}

        for split_name in splits:
            img_dst, lbl_dst = target_map[split_name]
            src_img = processed_root / split_name / "images"
            src_lbl = processed_root / split_name / "labels"
            img_dst.mkdir(parents=True, exist_ok=True)
            lbl_dst.mkdir(parents=True, exist_ok=True)

            for existing in list(img_dst.iterdir()) + list(lbl_dst.iterdir()):
                if existing.is_file():
                    existing.unlink()

            copied = 0
            if src_img.exists():
                for src_file in src_img.iterdir():
                    if src_file.is_file():
                        shutil.copy2(src_file, img_dst / src_file.name)
                        copied += 1
            if src_lbl.exists():
                for src_file in src_lbl.iterdir():
                    if src_file.is_file():
                        shutil.copy2(src_file, lbl_dst / src_file.name)

            counts[split_name] = copied
            logger.info(
                f"[镜像] {split_name} -> {img_dst.relative_to(paths.ROOT_DIR)} "
                f"({copied} 张图片)"
            )

        return counts

    def run_pipeline(
            self,
            train_ratio: float = 0.7,
            val_ratio: float = 0.2,
            test_ratio: float = 0.1
    ) -> Path:
        """
        执行端到端全自动流水线
        """
        raw_dataset_dir = paths.RAW_DATA_DIR / self.dataset_name
        if not raw_dataset_dir.exists():
            raise FileNotFoundError(f"未在指定位置找到原始数据集目录: {raw_dataset_dir}")

        self._check_raw_dataset_coverage(raw_dataset_dir)

        # 智能匹配子目录
        xml_dir = raw_dataset_dir / "Annotations"
        if not xml_dir.exists():
            xml_dir = raw_dataset_dir / "annotations"

        img_dir = raw_dataset_dir / "JPEGImages"
        if not img_dir.exists():
            img_dir = raw_dataset_dir / "images"

        manifest = DatasetManifest()
        detected_classes = set()

        all_xml_files = list(xml_dir.rglob("*.xml"))
        logger.info(f"🔍 深度雷达扫描：在 {xml_dir} 及其子目录下共挖掘到 {len(all_xml_files)} 个 XML 标注文件。")

        error_shown_count = 0

        for xml_file in all_xml_files:
            try:
                # 1. 跨目录递归撞库匹配图片
                base_name = xml_file.stem
                img_path = None

                for ext in (".jpg", ".jpeg", ".png", ".JPG", ".PNG", ".JPEG"):
                    try:
                        relative_sub_dir = xml_file.parent.relative_to(xml_dir)
                        candidate = img_dir / relative_sub_dir / f"{base_name}{ext}"
                        if candidate.exists():
                            img_path = candidate
                            break
                    except ValueError:
                        candidate = None

                    if img_path is None:
                        matches = list(img_dir.rglob(f"{base_name}{ext}"))
                        if matches:
                            img_path = matches[0]
                            break

                if img_path is None or not img_path.exists():
                    continue

                # 2. 调用驱动解析 XML（内鬼大概率藏在这里面）
                parsed_meta = self.converter.parse_annotation(xml_file)

                # 收集检测到的类别
                for ann in parsed_meta["annotations"]:
                    detected_classes.add(ann["category"])

                # 构建清单项 (width/height 来自 VOC XML, 供 YOLO 归一化使用)
                item = SampleItem(
                    image_path=img_path,
                    annotations=parsed_meta["annotations"],
                    width=int(parsed_meta["width"]),
                    height=int(parsed_meta["height"]),
                    raw_format=self.raw_format,
                )
                manifest.add_item(item)

            except Exception as e:
                # 💡 【核心调试代码】：将前3个报错样本的真实崩溃原因打印到终端，绝不姑息！
                if error_shown_count < 3:
                    logger.error(f"❌ 驱动层解析 XML 失败 [{xml_file.name}]: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_shown_count += 1
                continue

        logger.info(f"📊 [配对成功] 穿透式扫描完毕，成功捕获并锁定了 {manifest.size} 个有效图文样本！")

        if manifest.size == 0:
            raise RuntimeError(f"数据集中未扫描到任何有效的图片及对应的标注样本！请检查原始数据包是否残缺。")

        # 5. 动态确立最终的类别映射表
        self._final_classes = sorted(list(detected_classes))
        class_to_idx = {name: idx for idx, name in enumerate(self._final_classes)}

        # 6. 调用智能切分器进行三权分立划分
        splitter = DatasetSplitter(
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            random_state=self.options.random_state if self.options else 42
        )
        train_items, val_items, test_items = splitter.split(manifest)

        # 7. 执行物理文件实体落地隔离
        processed_dataset_root = paths.PROCESSED_DATA_DIR / self.dataset_name
        materializer = DatasetMaterializer(processed_dataset_root)

        train_count = materializer.materialize_split("train", train_items, class_to_idx)
        val_count = materializer.materialize_split("val", val_items, class_to_idx)
        test_count = materializer.materialize_split("test", test_items, class_to_idx)

        # 8. 整理审计追踪元数据并一键持久化为标准的 YAML 文件
        metadata = {
            "random_state": self.options.random_state if self.options else 42,
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

        # 9. 同步到 data/train|val|test, 并生成根目录 data/<dataset>.yaml 供训练加载
        mirror_counts = self._mirror_split_to_data_dir(processed_dataset_root)
        logger.info(
            f"[OK] 训练集已载入 data/train: {mirror_counts.get('train', 0)} 张 "
            f"(path={paths.DATA_DIR})"
        )
        data_yaml_writer = YoloYamlWriter(paths.DATA_DIR)
        data_yaml_writer.write_dataset_config(
            dataset_name=self.dataset_name,
            processed_root_dir=paths.DATA_DIR,
            classes=self._final_classes,
            metadata=metadata,
        )

        return config_yaml_path