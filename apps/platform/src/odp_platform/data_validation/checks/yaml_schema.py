# -*- coding: utf-8 -*-
"""check: yaml_schema — Ultralytics YAML 字段完整性。"""
from __future__ import annotations

from typing import Any, Dict, List

from odp_platform.data_validation.registry import (
    CheckContext,
    CheckResult,
    CheckSeverity,
    check,
)


def _names_valid(names: Any) -> bool:
    if names is None:
        return False
    if isinstance(names, list):
        return bool(names) and all(isinstance(n, str) and n.strip() for n in names)
    if isinstance(names, dict):
        return bool(names) and all(str(v).strip() for v in names.values())
    return False


@check("yaml_schema")
def validate_yaml_schema(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot

    if snap.yaml_load_error:
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary="YAML 无法加载",
            details={"problems": [snap.yaml_load_error]},
        )

    data = snap.yaml_data
    if not isinstance(data, dict):
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary="YAML 顶层不是 dict",
            details={"problems": [f"顶层类型: {type(data).__name__}"]},
        )

    problems: List[str] = []
    nc = data.get("nc")
    names = data.get("names")

    if not isinstance(nc, int) or isinstance(nc, bool) or nc <= 0:
        problems.append(f"nc 缺失或非法: {nc!r}")
    if not _names_valid(names):
        problems.append(f"names 缺失或非法: {type(names).__name__}")
    elif isinstance(nc, int) and not isinstance(nc, bool) and nc > 0:
        name_len = len(names) if isinstance(names, list) else len(names)
        if name_len != nc:
            problems.append(f"nc ({nc}) 跟 names 长度 ({name_len}) 不一致")

    if problems:
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary=f"YAML 字段问题 {len(problems)} 项",
            details={"problems": problems},
        )

    return CheckResult(
        name="yaml_schema",
        severity=CheckSeverity.PASS,
        summary="YAML 字段完整且一致",
        details={"nc": nc, "names_count": len(names) if isinstance(names, list) else len(names)},
    )
