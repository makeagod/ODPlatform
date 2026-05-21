# -*- coding: utf-8 -*-
"""ValidationReport 纯数据层。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from odp_platform.data_validation.registry import CheckResult, CheckSeverity
from odp_platform.data_validation.snapshot import DatasetSnapshot

_SEVERITY_RANK = (
    CheckSeverity.PASS,
    CheckSeverity.INFO,
    CheckSeverity.WARNING,
    CheckSeverity.ERROR,
)


@dataclass
class ValidationReport:
    run_id: str
    yaml_path: Path
    snapshot: DatasetSnapshot
    results: List[CheckResult]
    duration_seconds: float
    started_at_iso: str
    run_dir: Optional[Path] = None

    @property
    def counts_by_severity(self) -> Dict[str, int]:
        counts = {s: 0 for s in _SEVERITY_RANK}
        for r in self.results:
            counts[r.severity] = counts.get(r.severity, 0) + 1
        return counts

    @property
    def overall_severity(self) -> str:
        worst = CheckSeverity.PASS
        for r in self.results:
            if CheckSeverity.rank(r.severity) > CheckSeverity.rank(worst):
                worst = r.severity
        return worst

    @property
    def exit_code(self) -> int:
        sev = self.overall_severity
        if sev == CheckSeverity.ERROR:
            return 2
        if sev == CheckSeverity.WARNING:
            return 1
        return 0

    @property
    def failed_results(self) -> List[CheckResult]:
        return [r for r in self.results if not r.passed]

    @property
    def report_path(self) -> Optional[Path]:
        if self.run_dir is None:
            return None
        return self.run_dir / "report.json"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "yaml_path": str(self.yaml_path),
            "started_at_iso": self.started_at_iso,
            "duration_seconds": round(self.duration_seconds, 4),
            "overall_severity": self.overall_severity,
            "exit_code": self.exit_code,
            "counts_by_severity": self.counts_by_severity,
            "snapshot": {
                "data_root": str(self.snapshot.data_root),
                "nc": self.snapshot.nc,
                "class_names": list(self.snapshot.class_names),
                "task_type": self.snapshot.task_type,
                "splits": list(self.snapshot.splits),
                "total_images": self.snapshot.total_images,
                "scan_warnings": list(self.snapshot.scan_warnings),
            },
            "results": [
                {
                    "name": r.name,
                    "severity": r.severity,
                    "passed": r.passed,
                    "summary": r.summary,
                    "details": r.details,
                }
                for r in self.results
            ],
            "report_path": str(self.report_path) if self.report_path else None,
        }
