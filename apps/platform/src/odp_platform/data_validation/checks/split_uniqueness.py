# -*- coding: utf-8 -*-
"""check: split_uniqueness — train/val/test 图像 stem 泄露检测。"""
from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Set

from odp_platform.common.constants import DETAILS_PREVIEW_LIMIT
from odp_platform.data_validation.registry import (
    CheckContext,
    CheckResult,
    CheckSeverity,
    check,
)


@check("split_uniqueness")
def validate_split_uniqueness(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    stems_per_split: Dict[str, Set[str]] = {}

    for split in snap.splits:
        stems = {p.stem for p in snap.images_per_split.get(split, ())}
        stems_per_split[split] = stems

    overlaps: List[Dict[str, object]] = []
    total_duplicates = 0

    for a, b in combinations(sorted(stems_per_split.keys()), 2):
        dup = sorted(stems_per_split[a] & stems_per_split[b])
        if dup:
            total_duplicates += len(dup)
            overlaps.append(
                {
                    "splits": [a, b],
                    "count": len(dup),
                    "stems_preview": dup[:DETAILS_PREVIEW_LIMIT],
                }
            )

    details = {
        "splits": list(snap.splits),
        "total_duplicates": total_duplicates,
        "overlaps": overlaps,
    }

    if total_duplicates > 0:
        return CheckResult(
            name="split_uniqueness",
            severity=CheckSeverity.ERROR,
            summary=f"发现 {total_duplicates} 个跨 split 重复 stem",
            details=details,
        )

    return CheckResult(
        name="split_uniqueness",
        severity=CheckSeverity.PASS,
        summary="各 split 图像 stem 无交叉重复",
        details=details,
    )
