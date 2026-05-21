# -*- coding: utf-8 -*-
"""把 SplitManifest 落地到目标目录 (依赖注入, 不耦合 paths)。"""
from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from odp_platform.data_pipeline.split.manifest import PairList, SplitManifest

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SplitOutputDirs:
    train_images: Path
    train_labels: Path
    val_images: Path
    val_labels: Path
    test_images: Path
    test_labels: Path

    def mkdir_all(self) -> None:
        for p in (
            self.train_images, self.train_labels,
            self.val_images, self.val_labels,
            self.test_images, self.test_labels,
        ):
            p.mkdir(parents=True, exist_ok=True)


def _clear_files(directory: Path) -> None:
    if not directory.exists():
        return
    for f in directory.iterdir():
        if f.is_file():
            f.unlink()


def materialize(manifest: SplitManifest, output_dirs: SplitOutputDirs) -> dict:
    """把 manifest 的三组样本复制到 output_dirs。"""
    output_dirs.mkdir_all()

    counts = {
        "train": _copy_pairs(
            manifest.train,
            output_dirs.train_images,
            output_dirs.train_labels,
        ),
        "val": _copy_pairs(
            manifest.val,
            output_dirs.val_images,
            output_dirs.val_labels,
        ),
        "test": _copy_pairs(
            manifest.test,
            output_dirs.test_images,
            output_dirs.test_labels,
        ),
    }

    logger.info(
        f"materialize 完成: train={counts['train']}, "
        f"val={counts['val']}, test={counts['test']}"
    )
    return counts


def _copy_pairs(pairs: PairList, images_dst: Path, labels_dst: Path) -> int:
    _clear_files(images_dst)
    _clear_files(labels_dst)

    n_ok = 0
    for img_src, lbl_src in pairs:
        try:
            if img_src.exists():
                shutil.copy2(img_src, images_dst / img_src.name)
            if lbl_src.exists():
                shutil.copy2(lbl_src, labels_dst / lbl_src.name)
            n_ok += 1
        except OSError as e:
            logger.warning(f"复制失败 {img_src.name}: {e}")
    return n_ok
