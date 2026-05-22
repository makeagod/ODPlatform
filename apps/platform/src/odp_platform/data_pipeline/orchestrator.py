# -*- coding: utf-8 -*-
"""
数据准备流水线 Orchestrator (课程架构版)

流程: 格式转换 → 图文配对 → split_pairs → materialize → YAML
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from odp_platform.common import paths
from odp_platform.data_pipeline.registry import ConvertOptions
from odp_platform.data_pipeline.service import convert_data_to_yolo
from odp_platform.data_pipeline.split.manifest import PairList
from odp_platform.data_pipeline.split.materializer import SplitOutputDirs, materialize
from odp_platform.data_pipeline.split.splitter import split_pairs
from odp_platform.data_pipeline.split.yaml_writer import YoloYamlWriter

logger = logging.getLogger("odp-platform")


class DataPipelineOrchestrator:
    def __init__(self, dataset_name: str, raw_format: str, options: ConvertOptions | None = None):
        self.dataset_name = dataset_name
        self.raw_format = raw_format.lower()
        self.options = options or ConvertOptions()
        self._final_classes: List[str] = []

    def _resolve_raw_dirs(self, raw_root: Path) -> Tuple[Path, Path, Path]:
        xml_dir = raw_root / "Annotations"
        if not xml_dir.exists():
            xml_dir = raw_root / "annotations"

        img_dir = raw_root / "JPEGImages"
        if not img_dir.exists():
            img_dir = raw_root / "images"

        return raw_root, xml_dir, img_dir

    def _collect_pairs(
        self,
        img_dir: Path,
        labels_dir: Path,
        annotation_dir: Path | None = None,
    ) -> PairList:
        pairs: PairList = []
        label_map = {p.stem: p for p in labels_dir.glob("*.txt")}

        if annotation_dir and annotation_dir.exists():
            stems = [x.stem for x in annotation_dir.rglob("*.xml")]
        else:
            stems = list(label_map.keys())

        for stem in stems:
            lbl = label_map.get(stem)
            if lbl is None:
                continue

            img_path = None
            for ext in (".jpg", ".jpeg", ".png", ".JPG", ".PNG", ".JPEG"):
                if annotation_dir and annotation_dir.exists():
                    for xml in annotation_dir.rglob(f"{stem}.xml"):
                        rel = xml.parent.relative_to(annotation_dir)
                        candidate = img_dir / rel / f"{stem}{ext}"
                        if candidate.exists():
                            img_path = candidate
                            break
                if img_path is None:
                    matches = list(img_dir.rglob(f"{stem}{ext}"))
                    if matches:
                        img_path = matches[0]
                if img_path:
                    break

            if img_path and img_path.exists():
                pairs.append((img_path, lbl))

        return pairs

    def _mirror_split_to_data_dir(self, processed_root: Path) -> Dict[str, int]:
        target_map = {
            "train": (paths.TRAIN_IMAGES_DIR, paths.TRAIN_LABELS_DIR),
            "val": (paths.VAL_IMAGES_DIR, paths.VAL_LABELS_DIR),
            "test": (paths.TEST_IMAGES_DIR, paths.TEST_LABELS_DIR),
        }
        counts: Dict[str, int] = {}

        for split_name, (img_dst, lbl_dst) in target_map.items():
            src_img = processed_root / split_name / "images"
            src_lbl = processed_root / split_name / "labels"
            img_dst.mkdir(parents=True, exist_ok=True)
            lbl_dst.mkdir(parents=True, exist_ok=True)

            for d in (img_dst, lbl_dst):
                for f in d.iterdir():
                    if f.is_file():
                        f.unlink()

            copied = 0
            if src_img.exists():
                for f in src_img.iterdir():
                    if f.is_file():
                        shutil.copy2(f, img_dst / f.name)
                        copied += 1
            if src_lbl.exists():
                for f in src_lbl.iterdir():
                    if f.is_file():
                        shutil.copy2(f, lbl_dst / f.name)

            counts[split_name] = copied
            logger.info(
                f"[mirror] {split_name} -> {img_dst.relative_to(paths.ROOT_DIR)} ({copied} images)"
            )
        return counts

    def run_pipeline(
        self,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
    ) -> Path:
        raw_root = paths.RAW_DATA_DIR / self.dataset_name
        if not raw_root.exists():
            raise FileNotFoundError(f"未找到原始数据集: {raw_root}")

        _, xml_dir, img_dir = self._resolve_raw_dirs(raw_root)

        temp_labels = paths.TRANSFORM_TEMP_DIR / self.dataset_name / "labels"
        if temp_labels.exists():
            shutil.rmtree(temp_labels, ignore_errors=True)
        temp_labels.mkdir(parents=True, exist_ok=True)

        convert_input = xml_dir if xml_dir.exists() else raw_root
        logger.info(f"[1/4] 格式转换 {self.raw_format}: {convert_input} -> {temp_labels}")
        self._final_classes = convert_data_to_yolo(
            convert_input,
            temp_labels,
            self.raw_format,
            self.options,
        )

        logger.info("[2/4] 图文配对")
        pairs = self._collect_pairs(img_dir, temp_labels, convert_input)
        logger.info(f"配对成功 {len(pairs)} 对")

        if not pairs:
            raise RuntimeError("未扫描到有效的图片及标注样本, 请检查 data/raw 目录结构")

        logger.info(f"[3/4] 切分 train={train_ratio} val={val_ratio} test={test_ratio}")
        manifest = split_pairs(
            pairs,
            train_rate=train_ratio,
            val_rate=val_ratio,
            test_rate=test_ratio,
            random_state=self.options.random_state,
        )

        processed_root = paths.PROCESSED_DATA_DIR / self.dataset_name
        output_dirs = SplitOutputDirs(
            train_images=processed_root / "train" / "images",
            train_labels=processed_root / "train" / "labels",
            val_images=processed_root / "val" / "images",
            val_labels=processed_root / "val" / "labels",
            test_images=processed_root / "test" / "images",
            test_labels=processed_root / "test" / "labels",
        )

        logger.info(f"[4/4] 落盘 -> {processed_root}")
        split_counts = materialize(manifest, output_dirs)

        metadata = {
            "random_state": self.options.random_state,
            "split_counts": {**split_counts, "total_input": len(pairs)},
        }

        yaml_writer = YoloYamlWriter(paths.DATASET_CONFIGS_DIR)
        config_path = yaml_writer.write_dataset_config(
            dataset_name=self.dataset_name,
            processed_root_dir=processed_root,
            classes=self._final_classes,
            metadata=metadata,
        )

        mirror_counts = self._mirror_split_to_data_dir(processed_root)
        logger.info(f"[OK] data/train 已载入 {mirror_counts.get('train', 0)} 张")

        return config_path
