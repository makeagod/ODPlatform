# -*- coding: utf-8 -*-
"""check: pair_existence — 图像/标签成对，按缺失比例分级。"""
from __future__ import annotations

from odp_platform.common.constants import (
    DETAILS_PREVIEW_LIMIT,
    PAIR_MISSING_ERROR_RATIO,
    PAIR_MISSING_WARN_RATIO,
)
from odp_platform.data_validation.registry import (
    CheckContext,
    CheckResult,
    CheckSeverity,
    check,
)


@check("pair_existence")
def validate_pair_existence(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    missing_per_split: dict[str, int] = {}
    missing_examples: dict[str, list[str]] = {}
    total_images = 0
    total_missing = 0

    for split in snap.splits:
        images = snap.images_per_split.get(split, ())
        labels = snap.labels_per_split.get(split, ())
        split_missing: list[str] = []
        for img, lbl in zip(images, labels):
            total_images += 1
            if not lbl.is_file():
                total_missing += 1
                split_missing.append(img.name)
        missing_per_split[split] = len(split_missing)
        missing_examples[split] = split_missing[:DETAILS_PREVIEW_LIMIT]

    if total_images == 0:
        return CheckResult(
            name="pair_existence",
            severity=CheckSeverity.WARNING,
            summary="未扫描到任何图像",
            details={"total_images": 0, "total_missing": 0, "missing_ratio": 0.0},
        )

    missing_ratio = total_missing / total_images
    thresholds = {
        "warn_ratio": PAIR_MISSING_WARN_RATIO,
        "error_ratio": PAIR_MISSING_ERROR_RATIO,
    }
    details = {
        "total_images": total_images,
        "total_missing": total_missing,
        "missing_ratio": round(missing_ratio, 6),
        "thresholds": thresholds,
        "missing_per_split": missing_per_split,
        "missing_examples": missing_examples,
    }

    if total_missing == 0:
        severity = CheckSeverity.PASS
        summary = "全部图像均有对应标签文件"
    elif missing_ratio >= PAIR_MISSING_ERROR_RATIO:
        severity = CheckSeverity.ERROR
        summary = f"缺失比例 {missing_ratio:.1%} ≥ 错误阈值"
    elif missing_ratio >= PAIR_MISSING_WARN_RATIO:
        severity = CheckSeverity.WARNING
        summary = f"缺失比例 {missing_ratio:.1%} ≥ 警告阈值"
    elif missing_ratio > 0:
        severity = CheckSeverity.INFO
        summary = f"少量缺失 {total_missing}/{total_images}"
    else:
        severity = CheckSeverity.PASS
        summary = "成对完整"

    return CheckResult(
        name="pair_existence",
        severity=severity,
        summary=summary,
        details=details,
    )
