# -*- coding: utf-8 -*-
"""训练/验证指标 dataclass 与日志输出。"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from odp_platform.common.constants import Task
from odp_platform.common.string_utils import pad_to_width

logger = logging.getLogger(__name__)

_METRIC_FIELDS_BY_TASK: dict[str, list[tuple[str, str]]] = {
    Task.DETECT: [
        ("metrics/precision(B)", "Precision(B)"),
        ("metrics/recall(B)", "Recall(B)"),
        ("metrics/mAP50(B)", "mAP50(B)"),
        ("metrics/mAP50-95(B)", "mAP50-95(B)"),
    ],
    Task.SEGMENT: [
        ("metrics/precision(B)", "Precision(B)"),
        ("metrics/recall(B)", "Recall(B)"),
        ("metrics/mAP50(B)", "mAP50(B)"),
        ("metrics/mAP50-95(B)", "mAP50-95(B)"),
        ("metrics/precision(M)", "Precision(M)"),
        ("metrics/recall(M)", "Recall(M)"),
        ("metrics/mAP50(M)", "mAP50(M)"),
        ("metrics/mAP50-95(M)", "mAP50-95(M)"),
    ],
}


def _safe_float(value: Any, default: float = math.nan) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class TrainMetrics:
    task: str
    save_dir: Path
    timestamp: str
    speed_ms: dict[str, float]
    overall: dict[str, float]
    class_map_50_95: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_yolo_results(
        cls,
        results: Any,
        model_trainer: Any = None,
    ) -> "TrainMetrics":
        task = getattr(results, "task", "unknown")

        save_dir_raw = getattr(results, "save_dir", None)
        if save_dir_raw is None and model_trainer is not None:
            save_dir_raw = getattr(model_trainer, "save_dir", None)
        save_dir = Path(save_dir_raw) if save_dir_raw is not None else Path("unknown")

        speed_raw = getattr(results, "speed", {}) or {}
        speed_ms: dict[str, float] = {
            "preprocess": _safe_float(speed_raw.get("preprocess")),
            "inference": _safe_float(speed_raw.get("inference")),
            "loss": _safe_float(speed_raw.get("loss")),
            "postprocess": _safe_float(speed_raw.get("postprocess")),
        }
        valid = [v for v in speed_ms.values() if not math.isnan(v)]
        speed_ms["total"] = sum(valid) if valid else math.nan

        results_dict = getattr(results, "results_dict", {}) or {}
        overall: dict[str, float] = {
            "fitness": _safe_float(getattr(results, "fitness", None)),
        }
        for k, v in results_dict.items():
            overall[k] = _safe_float(v)

        class_map: dict[str, float] = {}
        names = getattr(results, "names", {}) or {}
        maps = getattr(results, "maps", np.array([]))
        if names and hasattr(maps, "size") and maps.size > 0:
            for idx, class_name in names.items():
                if idx < maps.size:
                    class_map[class_name] = _safe_float(maps[idx])

        return cls(
            task=task,
            save_dir=save_dir,
            timestamp=datetime.now().isoformat(timespec="seconds"),
            speed_ms=speed_ms,
            overall=overall,
            class_map_50_95=class_map,
        )

    def to_dict(self) -> dict[str, Any]:
        def _clean_nan(d: dict[str, float]) -> dict[str, float | None]:
            return {
                k: (None if isinstance(v, float) and math.isnan(v) else v)
                for k, v in d.items()
            }

        return {
            "task": self.task,
            "save_dir": str(self.save_dir),
            "timestamp": self.timestamp,
            "speed_ms": _clean_nan(self.speed_ms),
            "overall": _clean_nan(self.overall),
            "class_map_50_95": _clean_nan(self.class_map_50_95),
        }


def log_train_metrics(
    metrics: TrainMetrics,
    *,
    logger: logging.Logger | None = None,
    key_width: int = 20,
    section_width: int = 60,
) -> None:
    log = logger or logging.getLogger(__name__)
    line = "=" * section_width
    thin = "-" * section_width

    log.info(line)
    log.info(f"训练结果 ({metrics.task.capitalize()} Task)".center(section_width))
    log.info(line)

    log.info("基本信息".center(section_width))
    log.info(thin)
    log.info(f"{pad_to_width('任务类型', key_width)}: {metrics.task}")
    log.info(f"{pad_to_width('保存目录', key_width)}: {metrics.save_dir}")
    log.info(f"{pad_to_width('时间戳', key_width)}: {metrics.timestamp}")

    log.info("处理速度 (ms/image)".center(section_width))
    log.info(thin)
    for k_disp, k_data in [
        ("预处理", "preprocess"),
        ("推理", "inference"),
        ("损失计算", "loss"),
        ("后处理", "postprocess"),
        ("总计", "total"),
    ]:
        val = metrics.speed_ms.get(k_data, math.nan)
        log.info(f"{pad_to_width(k_disp, key_width)}: {val:.3f} ms")

    log.info("整体评估指标".center(section_width))
    log.info(thin)
    log.info(
        f"{pad_to_width('Fitness 分数', key_width)}: "
        f"{metrics.overall.get('fitness', math.nan):.4f}"
    )

    metric_fields = _METRIC_FIELDS_BY_TASK.get(metrics.task, [])
    if metric_fields:
        for raw_key, display in metric_fields:
            log.info(
                f"{pad_to_width(display, key_width)}: "
                f"{metrics.overall.get(raw_key, math.nan):.4f}"
            )
    else:
        for k, v in metrics.overall.items():
            if k == "fitness":
                continue
            log.info(f"{pad_to_width(k, key_width)}: {v:.4f}")

    if metrics.class_map_50_95:
        log.info("类别级 mAP@0.5:0.95 (Box)".center(section_width))
        log.info(thin)
        valid = {
            k: v for k, v in metrics.class_map_50_95.items() if not math.isnan(v)
        }
        if valid:
            for class_name, mAP in sorted(
                valid.items(), key=lambda kv: kv[1], reverse=True
            ):
                log.info(f"{pad_to_width(class_name, key_width)}: {mAP:.4f}")

    log.info(line)
