# -*- coding: utf-8 -*-
"""check: label_format — YOLO 标签行格式（detect / segment）。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from odp_platform.common.constants import DETAILS_PREVIEW_LIMIT, Task
from odp_platform.data_validation.registry import (
    CheckContext,
    CheckResult,
    CheckSeverity,
    check,
)

ERR_FIELD_COUNT = "field_count_mismatch"
ERR_PARSE = "parse_error"
ERR_CLASS = "class_id_out_of_range"
ERR_COORD = "coord_out_of_range"
ERR_POLY = "polygon_too_few_points"


def _validate_detect_line(parts: List[str], nc: int) -> str | None:
    if len(parts) != 5:
        return ERR_FIELD_COUNT
    try:
        cls = int(parts[0])
        coords = [float(x) for x in parts[1:]]
    except ValueError:
        return ERR_PARSE
    if cls < 0 or cls >= nc:
        return ERR_CLASS
    if any(c < 0 or c > 1 for c in coords):
        return ERR_COORD
    return None


def _validate_segment_line(parts: List[str], nc: int) -> str | None:
    if len(parts) < 8 or (len(parts) - 1) % 2 != 0:
        return ERR_FIELD_COUNT
    try:
        cls = int(parts[0])
        coords = [float(x) for x in parts[1:]]
    except ValueError:
        return ERR_PARSE
    n_points = len(coords) // 2
    if n_points < 3:
        return ERR_POLY
    if cls < 0 or cls >= nc:
        return ERR_CLASS
    if any(c < 0 or c > 1 for c in coords):
        return ERR_COORD
    return None


def _scan_label_file(
    label_path: Path,
    task: str,
    nc: int,
) -> Tuple[int, List[Dict[str, object]]]:
    errors: List[Dict[str, object]] = []
    total_lines = 0
    if not label_path.is_file():
        return 0, errors
    try:
        text = label_path.read_text(encoding="utf-8")
    except OSError as exc:
        return 0, [
            {
                "file": label_path.name,
                "line": 0,
                "error_kind": ERR_PARSE,
                "message": str(exc),
            }
        ]
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        total_lines += 1
        parts = stripped.split()
        if task == Task.SEGMENT:
            kind = _validate_segment_line(parts, nc)
        else:
            kind = _validate_detect_line(parts, nc)
        if kind:
            errors.append(
                {
                    "file": label_path.name,
                    "line": line_no,
                    "error_kind": kind,
                }
            )
    return total_lines, errors


@check("label_format")
def validate_label_format(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    nc = snap.nc

    if nc is None or nc <= 0:
        return CheckResult(
            name="label_format",
            severity=CheckSeverity.INFO,
            summary="nc 无效，跳过 label_format（由 yaml_schema 负责）",
            details={"task_type": snap.task_type, "skipped": True},
        )

    total_lines = 0
    total_errors = 0
    error_kinds: Dict[str, int] = {}
    errors_preview: List[Dict[str, object]] = []

    for split in snap.splits:
        for lbl in snap.labels_per_split.get(split, ()):
            if not lbl.is_file():
                continue
            lines, errs = _scan_label_file(lbl, snap.task_type, nc)
            total_lines += lines
            total_errors += len(errs)
            for e in errs:
                kind = str(e["error_kind"])
                error_kinds[kind] = error_kinds.get(kind, 0) + 1
                if len(errors_preview) < DETAILS_PREVIEW_LIMIT:
                    errors_preview.append(e)

    if total_errors == 0:
        return CheckResult(
            name="label_format",
            severity=CheckSeverity.PASS,
            summary=f"共 {total_lines} 行标签格式合法",
            details={
                "task_type": snap.task_type,
                "total_lines": total_lines,
                "total_errors": 0,
                "error_kinds": error_kinds,
                "errors_preview": [],
            },
        )

    return CheckResult(
        name="label_format",
        severity=CheckSeverity.ERROR,
        summary=f"发现 {total_errors} 处标签格式错误",
        details={
            "task_type": snap.task_type,
            "total_lines": total_lines,
            "total_errors": total_errors,
            "error_kinds": error_kinds,
            "errors_preview": errors_preview,
        },
    )
