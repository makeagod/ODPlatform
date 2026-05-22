# -*- coding: utf-8 -*-
"""DatasetSnapshot — 一次扫描，多次复用（best-effort，不抛异常）。"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from odp_platform.common.constants import IMAGE_EXTENSIONS, Task
from odp_platform.common.performance_utils import time_it

logger = logging.getLogger(__name__)

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
    scan_warnings: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def splits(self) -> Tuple[str, ...]:
        return tuple(s for s in _SPLIT_ORDER if s in self.images_per_split)

    @property
    def total_images(self) -> int:
        return sum(len(imgs) for imgs in self.images_per_split.values())


def _load_yaml(yaml_path: Path) -> Tuple[Dict[str, Any], Optional[str]]:
    if not yaml_path.exists():
        return {}, f"yaml 文件不存在: {yaml_path}"
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            return {}, f"yaml 顶层不是 dict: {type(data).__name__}"
        return data, None
    except yaml.YAMLError as exc:
        return {}, f"yaml 解析失败: {exc}"
    except OSError as exc:
        return {}, f"yaml 读取失败: {exc}"


def _resolve_data_root(yaml_path: Path, yaml_data: Dict[str, Any]) -> Path:
    path_str = yaml_data.get("path")
    if not path_str:
        return yaml_path.parent.resolve()
    p = Path(str(path_str))
    return p.resolve() if p.is_absolute() else (yaml_path.parent / p).resolve()


def _resolve_split_dir(data_root: Path, split_field: Any) -> Optional[Path]:
    if not isinstance(split_field, str) or not str(split_field).strip():
        return None
    p = Path(split_field)
    return p.resolve() if p.is_absolute() else (data_root / p).resolve()


def _list_images(split_dir: Path) -> List[Path]:
    if not split_dir.is_dir():
        return []
    images: List[Path] = []
    for ext in IMAGE_EXTENSIONS:
        images.extend(split_dir.glob(f"*{ext}"))
    return sorted({p.resolve() for p in images})


def _label_path_for_image(image_path: Path) -> Path:
    parts = list(image_path.parts)
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "images":
            parts[i] = "labels"
            break
    return Path(*parts[:-1]) / f"{image_path.stem}.txt"


def _normalize_names(names_raw: Any) -> Tuple[str, ...]:
    if isinstance(names_raw, list) and all(isinstance(n, str) for n in names_raw):
        return tuple(names_raw)
    if isinstance(names_raw, dict):
        if all(isinstance(k, int) for k in names_raw) and all(
            isinstance(v, str) for v in names_raw.values()
        ):
            return tuple(v for _, v in sorted(names_raw.items()))
    return ()


def _parse_nc(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return value
    return None


def _build_split_stats(images: List[Path], labels: List[Path]) -> SplitStats:
    annotated = 0
    instances = 0
    for lbl in labels:
        if not lbl.exists():
            continue
        try:
            content = lbl.read_text(encoding="utf-8")
        except OSError:
            continue
        lines = [ln for ln in content.splitlines() if ln.strip()]
        if not lines:
            continue
        annotated += 1
        instances += len(lines)
    return SplitStats(
        image_count=len(images),
        annotated_count=annotated,
        total_instances=instances,
    )


@time_it(name="build_snapshot")
def build_snapshot(
    yaml_path: Path,
    task_type: Optional[str] = None,
) -> DatasetSnapshot:
    yaml_path = yaml_path.resolve()
    warnings: List[str] = []

    yaml_data, yaml_err = _load_yaml(yaml_path)
    if yaml_err:
        warnings.append(yaml_err)

    data_root = _resolve_data_root(yaml_path, yaml_data)
    nc = _parse_nc(yaml_data.get("nc"))
    class_names = _normalize_names(yaml_data.get("names"))

    resolved_task = task_type or yaml_data.get("task") or Task.DETECT
    if resolved_task not in (Task.DETECT, Task.SEGMENT):
        warnings.append(f"未知 task_type '{resolved_task}', 回退到 '{Task.DETECT}'")
        resolved_task = Task.DETECT

    images_per_split: Dict[str, Tuple[Path, ...]] = {}
    labels_per_split: Dict[str, Tuple[Path, ...]] = {}
    stats_per_split: Dict[str, SplitStats] = {}

    for split in _SPLIT_ORDER:
        split_dir = _resolve_split_dir(data_root, yaml_data.get(split))
        if split_dir is None or not split_dir.is_dir():
            if split in yaml_data:
                warnings.append(f"split '{split}' 目录不可用: {split_dir}")
            continue

        images = _list_images(split_dir)
        if not images:
            warnings.append(f"split '{split}' 目录下无图像: {split_dir}")
            continue

        labels = [_label_path_for_image(img) for img in images]
        images_per_split[split] = tuple(images)
        labels_per_split[split] = tuple(labels)
        stats_per_split[split] = _build_split_stats(images, labels)

    snapshot = DatasetSnapshot(
        yaml_path=yaml_path,
        yaml_data=yaml_data,
        yaml_load_error=yaml_err,
        data_root=data_root,
        nc=nc,
        class_names=class_names,
        task_type=resolved_task,
        images_per_split=images_per_split,
        labels_per_split=labels_per_split,
        stats_per_split=stats_per_split,
        scan_warnings=tuple(warnings),
    )
    logger.info(
        "snapshot 构建完成: %d 张图像, splits=%s, task=%s",
        snapshot.total_images,
        list(snapshot.splits),
        resolved_task,
    )
    return snapshot
