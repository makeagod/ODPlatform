# -*- coding: utf-8 -*-
"""框架占位 check（验证注册表机制）；可与业务 check 并存。"""
from odp_platform.data_validation.registry import (
    CheckContext,
    CheckResult,
    CheckSeverity,
    check,
)


@check("placeholder")
def placeholder_check(ctx: CheckContext) -> CheckResult:
    return CheckResult(
        name="placeholder",
        severity=CheckSeverity.PASS,
        summary="占位检测：注册表与调度机制工作正常",
        details={"yaml_path": str(ctx.yaml_path)},
    )
