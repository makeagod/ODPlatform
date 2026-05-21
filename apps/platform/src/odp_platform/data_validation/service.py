# -*- coding: utf-8 -*-
"""调度层：聚合执行全部 check + validate_dataset 端到端。"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from odp_platform.common.paths import validation_run_dir
from odp_platform.common.performance_utils import time_it
from odp_platform.common.system_utils import log_device_info
from odp_platform.data_validation.registry import (
    CheckContext,
    CheckResult,
    CheckSeverity,
    iter_checks,
)
from odp_platform.data_validation.report import ValidationReport
from odp_platform.data_validation.snapshot import DatasetSnapshot, build_snapshot

logger = logging.getLogger(__name__)


def _make_run_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:21]


def _safe_run_one(entry, ctx: CheckContext) -> CheckResult:
    try:
        return entry.func(ctx)
    except Exception as exc:
        return CheckResult(
            name=entry.name,
            severity=CheckSeverity.ERROR,
            summary=f"{entry.name} 执行异常: {exc}",
            details={
                "exception_type": type(exc).__name__,
                "message": str(exc),
            },
        )


@time_it(name="run_all_checks")
def run_all_checks(ctx: CheckContext) -> List[CheckResult]:
    results: List[CheckResult] = []
    for entry in iter_checks():
        results.append(_safe_run_one(entry, ctx))
    return results


def validate_dataset(
    yaml_path: Path,
    task_type: Optional[str] = None,
    run_id: Optional[str] = None,
    run_dir: Optional[Path] = None,
    write_report: bool = True,
) -> ValidationReport:
    log_device_info(logger)
    started = time.perf_counter()
    started_iso = datetime.now(timezone.utc).isoformat()

    rid = run_id or _make_run_id()
    rdir = run_dir or validation_run_dir(rid)

    snapshot: DatasetSnapshot = build_snapshot(yaml_path, task_type=task_type)
    ctx = CheckContext(yaml_path=yaml_path.resolve(), snapshot=snapshot)
    results = run_all_checks(ctx)
    duration = time.perf_counter() - started

    report = ValidationReport(
        run_id=rid,
        yaml_path=yaml_path.resolve(),
        snapshot=snapshot,
        results=results,
        duration_seconds=duration,
        started_at_iso=started_iso,
        run_dir=rdir,
    )

    if write_report and report.report_path is not None:
        report.report_path.parent.mkdir(parents=True, exist_ok=True)
        report.report_path.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("JSON 报告已写入: %s", report.report_path)

    return report
