# -*- coding: utf-8 -*-
"""pair_existence — 验证每张图都有对应 .txt 标签（按缺失比例分级）。"""
from __future__ import annotations

from typing import Any, Dict, List

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

    if not snap.images_per_split:
        return CheckResult(
            name="pair_existence",
            severity=CheckSeverity.INFO,
            summary="无任何 split 可检查 (snapshot 为空)",
            details={"reason": "empty_snapshot"},
        )

    orphan_per_split: Dict[str, List[str]] = {}
    total_images = 0
    total_missing = 0

    for split, images in snap.images_per_split.items():
        labels = snap.labels_per_split.get(split, ())
        missing_in_split: List[str] = []
        for img, lbl in zip(images, labels):
            total_images += 1
            if not lbl.exists():
                total_missing += 1
                missing_in_split.append(str(img))
        if missing_in_split:
            orphan_per_split[split] = missing_in_split

    missing_ratio = total_missing / max(total_images, 1)

    if total_missing == 0:
        severity = CheckSeverity.PASS
        summary = f"全部 {total_images} 张图像都有对应标签"
    elif missing_ratio >= PAIR_MISSING_ERROR_RATIO:
        severity = CheckSeverity.ERROR
        summary = (
            f"缺标签比例 {missing_ratio:.1%} ≥ {PAIR_MISSING_ERROR_RATIO:.0%} "
            f"({total_missing}/{total_images} 张图无标签)"
        )
    elif missing_ratio >= PAIR_MISSING_WARN_RATIO:
        severity = CheckSeverity.WARNING
        summary = (
            f"缺标签比例 {missing_ratio:.1%} ≥ {PAIR_MISSING_WARN_RATIO:.0%} "
            f"({total_missing}/{total_images} 张图无标签)"
        )
    else:
        severity = CheckSeverity.INFO
        summary = (
            f"少量标签缺失 ({total_missing}/{total_images} = {missing_ratio:.2%})"
        )

    details: Dict[str, Any] = {
        "total_images": total_images,
        "total_missing": total_missing,
        "missing_ratio": round(missing_ratio, 4),
        "thresholds": {
            "error_at": PAIR_MISSING_ERROR_RATIO,
            "warn_at": PAIR_MISSING_WARN_RATIO,
        },
        "missing_per_split": {
            split: len(orphans) for split, orphans in orphan_per_split.items()
        },
    }
    if orphan_per_split:
        details["missing_examples"] = {
            split: orphans[:DETAILS_PREVIEW_LIMIT]
            for split, orphans in orphan_per_split.items()
        }

    return CheckResult(
        name="pair_existence",
        severity=severity,
        summary=summary,
        details=details,
    )
