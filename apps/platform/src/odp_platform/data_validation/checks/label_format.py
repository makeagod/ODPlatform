# -*- coding: utf-8 -*-
"""label_format — 验证每行 .txt 格式（detect / segment）。"""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from odp_platform.common.constants import DETAILS_PREVIEW_LIMIT, Task
from odp_platform.data_validation.registry import (
    CheckContext,
    CheckResult,
    CheckSeverity,
    check,
)

KIND_FIELD_COUNT_MISMATCH = "field_count_mismatch"
KIND_PARSE_ERROR = "parse_error"
KIND_CLASS_ID_OUT_OF_RANGE = "class_id_out_of_range"
KIND_COORD_OUT_OF_RANGE = "coord_out_of_range"
KIND_POLYGON_TOO_FEW = "polygon_too_few_points"


@check("label_format")
def validate_label_format(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot

    if snap.nc is None or snap.nc <= 0:
        return CheckResult(
            name="label_format",
            severity=CheckSeverity.INFO,
            summary="缺少合法 nc, 跳过 label_format (yaml_schema 应已报告)",
            details={"reason": "nc_unavailable"},
        )

    task_type = snap.task_type
    errors: List[Dict[str, Any]] = []
    error_kinds: Counter = Counter()
    total_lines = 0

    for _split, labels in snap.labels_per_split.items():
        for lbl in labels:
            if not lbl.exists():
                continue
            try:
                content = lbl.read_text(encoding="utf-8")
            except OSError:
                continue
            for line_no, line in enumerate(content.splitlines(), 1):
                line = line.strip()
                if not line:
                    continue
                total_lines += 1
                err = _validate_one_line(line, task_type, snap.nc)
                if err is not None:
                    kind, detail = err
                    error_kinds[kind] += 1
                    if len(errors) < DETAILS_PREVIEW_LIMIT:
                        errors.append({
                            "label": str(lbl),
                            "line_no": line_no,
                            "kind": kind,
                            "detail": detail,
                        })

    if not error_kinds:
        return CheckResult(
            name="label_format",
            severity=CheckSeverity.PASS,
            summary=f"全部 {total_lines} 行标签格式正确 (task={task_type})",
            details={"task_type": task_type, "total_lines": total_lines},
        )

    total_errors = sum(error_kinds.values())
    return CheckResult(
        name="label_format",
        severity=CheckSeverity.ERROR,
        summary=f"{total_errors}/{total_lines} 行标签格式错误 (task={task_type})",
        details={
            "task_type": task_type,
            "total_lines": total_lines,
            "total_errors": total_errors,
            "error_kinds": dict(error_kinds),
            "errors_preview": errors,
        },
    )


def _validate_one_line(line: str, task_type: str, nc: int) -> Optional[Tuple[str, str]]:
    parts = line.split()

    if task_type == Task.DETECT:
        if len(parts) != 5:
            return KIND_FIELD_COUNT_MISMATCH, f"detect 要求 5 字段, 实际 {len(parts)}"
        try:
            cls_id = int(parts[0])
            coords = [float(x) for x in parts[1:5]]
        except ValueError as exc:
            return KIND_PARSE_ERROR, f"字段类型错: {exc}"
        if not (0 <= cls_id < nc):
            return KIND_CLASS_ID_OUT_OF_RANGE, f"cls_id={cls_id} 不在 [0,{nc})"
        if not all(0.0 <= c <= 1.0 for c in coords):
            bad = [round(c, 4) for c in coords if not (0.0 <= c <= 1.0)]
            return KIND_COORD_OUT_OF_RANGE, f"坐标越界 [0,1]: {bad}"
        return None

    if task_type == Task.SEGMENT:
        if len(parts) < 7 or (len(parts) - 1) % 2 != 0:
            if len(parts) < 7:
                return KIND_POLYGON_TOO_FEW, f"segment 至少 3 点 (7 字段), 实际 {len(parts)}"
            return KIND_FIELD_COUNT_MISMATCH, f"segment 字段数应为 1+2N, 实际 {len(parts)}"
        try:
            cls_id = int(parts[0])
            coords = [float(x) for x in parts[1:]]
        except ValueError as exc:
            return KIND_PARSE_ERROR, f"字段类型错: {exc}"
        if not (0 <= cls_id < nc):
            return KIND_CLASS_ID_OUT_OF_RANGE, f"cls_id={cls_id} 不在 [0,{nc})"
        if not all(0.0 <= c <= 1.0 for c in coords):
            bad_count = sum(1 for c in coords if not (0.0 <= c <= 1.0))
            return KIND_COORD_OUT_OF_RANGE, f"{bad_count}/{len(coords)} 个坐标越界 [0,1]"
        return None

    return KIND_PARSE_ERROR, f"未知 task_type: {task_type}"
