# -*- coding: utf-8 -*-
"""DatasetSnapshot 一次扫描，best-effort 不抛异常。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

from odp_platform.common.constants import IMAGE_EXTENSIONS, Task
from odp_platform.common.performance_utils import time_it

_SPLIT_ORDER = ("train", "val", "test")


@dataclass(frozen=True)
class SplitStats:
    image_count: int
    annotated_count: int
    total_instances: int


@dataclass(frozen=True)
class DatasetSnapshot:
    yaml_path: Path
    yaml_data: Dict[str, Any]
    yaml_load_error: Optional[str]
    data_root: Path
    nc: Optional[int]
    class_names: Tuple[str, ...]
    task_type: str
    images_per_split: Dict[str, Tuple[Path, ...]]
    labels_per_split: Dict[str, Tuple[Path, ...]]
    stats_per_split: Dict[str, SplitStats]
    scan_warnings: Tuple[str, ...]

    @property
    def splits(self) -> Tuple[str, ...]:
        present = [s for s in _SPLIT_ORDER if s in self.images_per_split]
        extra = sorted(k for k in self.images_per_split if k not in _SPLIT_ORDER)
        return tuple(present + extra)

    @property
    def total_images(self) -> int:
        return sum(len(v) for v in self.images_per_split.values())


def _normalize_names(names: Any) -> Tuple[str, ...]:
    if names is None:
        return ()
    if isinstance(names, dict):
        keys = sorted(names.keys(), key=lambda k: int(k) if str(k).isdigit() else str(k))
        return tuple(str(names[k]) for k in keys)
    if isinstance(names, list):
        return tuple(str(n) for n in names)
    return ()


def _parse_nc(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return value
    return None


def _list_images(images_dir: Path) -> Tuple[Path, ...]:
    if not images_dir.is_dir():
        return ()
    found: list[Path] = []
    for ext in IMAGE_EXTENSIONS:
        found.extend(images_dir.glob(f"*{ext}"))
    return tuple(sorted({p.resolve() for p in found}))


def _labels_dir_for(images_dir: Path) -> Path:
    parts = list(images_dir.parts)
    if parts and parts[-1].lower() == "images":
        return Path(*parts[:-1]) / "labels"
    return images_dir.parent / "labels"


def _count_label_stats(label_paths: Tuple[Path, ...]) -> SplitStats:
    annotated = 0
    instances = 0
    for lp in label_paths:
        if not lp.is_file():
            continue
        try:
            text = lp.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if text:
            annotated += 1
            instances += len([ln for ln in text.splitlines() if ln.strip()])
    return SplitStats(
        image_count=0,
        annotated_count=annotated,
        total_instances=instances,
    )


@time_it(name="build_snapshot")
def build_snapshot(yaml_path: Path, task_type: Optional[str] = None) -> DatasetSnapshot:
    yaml_data: Dict[str, Any] = {}
    yaml_load_error: Optional[str] = None
    scan_warnings: list[str] = []

    if not yaml_path.exists():
        yaml_load_error = f"YAML 文件不存在: {yaml_path}"
    else:
        try:
            raw = yaml_path.read_text(encoding="utf-8")
            loaded = yaml.safe_load(raw)
            if loaded is None:
                yaml_data = {}
            elif isinstance(loaded, dict):
                yaml_data = loaded
            else:
                yaml_load_error = f"YAML 顶层类型非法: {type(loaded).__name__}"
        except yaml.YAMLError as exc:
            yaml_load_error = str(exc)

    resolved_task = task_type or str(yaml_data.get("task", Task.DETECT))
    if resolved_task not in (Task.DETECT, Task.SEGMENT):
        resolved_task = Task.DETECT

    data_root = Path(str(yaml_data.get("path", yaml_path.parent)))
    if not data_root.is_absolute():
        data_root = (yaml_path.parent / data_root).resolve()

    nc = _parse_nc(yaml_data.get("nc"))
    class_names = _normalize_names(yaml_data.get("names"))

    images_per_split: Dict[str, Tuple[Path, ...]] = {}
    labels_per_split: Dict[str, Tuple[Path, ...]] = {}
    stats_per_split: Dict[str, SplitStats] = {}

    for split in _SPLIT_ORDER:
        rel = yaml_data.get(split)
        if not rel:
            continue
        images_dir = (data_root / str(rel)).resolve()
        if not images_dir.is_dir():
            scan_warnings.append(f"{split}: 图像目录不存在 {images_dir}")
            images_per_split[split] = ()
            labels_per_split[split] = ()
            stats_per_split[split] = SplitStats(0, 0, 0)
            continue

        images = _list_images(images_dir)
        labels_dir = _labels_dir_for(images_dir)
        label_paths = tuple(
            (labels_dir / f"{img.stem}.txt").resolve() for img in images
        )
        label_stats = _count_label_stats(label_paths)
        stats_per_split[split] = SplitStats(
            image_count=len(images),
            annotated_count=label_stats.annotated_count,
            total_instances=label_stats.total_instances,
        )
        images_per_split[split] = images
        labels_per_split[split] = label_paths

    return DatasetSnapshot(
        yaml_path=yaml_path.resolve(),
        yaml_data=yaml_data,
        yaml_load_error=yaml_load_error,
        data_root=data_root,
        nc=nc,
        class_names=class_names,
        task_type=resolved_task,
        images_per_split=images_per_split,
        labels_per_split=labels_per_split,
        stats_per_split=stats_per_split,
        scan_warnings=tuple(scan_warnings),
    )
