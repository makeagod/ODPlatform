# -*- coding: utf-8 -*-
"""ValidationReport → 三段式日志展示。"""
from __future__ import annotations

import logging

from odp_platform.data_validation.registry import CheckSeverity
from odp_platform.data_validation.report import ValidationReport

logger = logging.getLogger(__name__)


def _log_level_for(severity: str) -> int:
    if severity == CheckSeverity.ERROR:
        return logging.ERROR
    if severity == CheckSeverity.WARNING:
        return logging.WARNING
    if severity == CheckSeverity.INFO:
        return logging.INFO
    return logging.DEBUG


def _render_dataset_summary(report: ValidationReport) -> None:
    snap = report.snapshot
    logger.info("=" * 60)
    logger.info("【数据集摘要】")
    logger.info("  YAML: %s", report.yaml_path)
    logger.info("  数据根: %s", snap.data_root)
    logger.info("  任务: %s | nc=%s | 类别=%s", snap.task_type, snap.nc, snap.class_names)
    for split in snap.splits:
        st = snap.stats_per_split.get(split)
        if st:
            logger.info(
                "  %s: images=%d annotated=%d instances=%d",
                split,
                st.image_count,
                st.annotated_count,
                st.total_instances,
            )
    if snap.scan_warnings:
        for w in snap.scan_warnings:
            logger.warning("  扫描警告: %s", w)
    logger.info("  总图像数: %d", snap.total_images)


def _render_checks_overview(report: ValidationReport) -> None:
    logger.info("-" * 60)
    logger.info("【检查一览】")
    for r in report.results:
        line = f"  [{r.severity:7}] {r.name}: {r.summary}"
        # 集中摘要一律 INFO，便于验收看到全部 check（含 PASS）
        logger.info(line)


def _render_failure_details(report: ValidationReport) -> None:
    failed = [r for r in report.results if r.severity in (CheckSeverity.ERROR, CheckSeverity.WARNING)]
    if not failed:
        return
    logger.info("-" * 60)
    logger.info("【失败详情】")
    for r in failed:
        logger.info("  >> %s (%s)", r.name, r.severity)
        for key, val in r.details.items():
            if isinstance(val, (list, dict)) and len(str(val)) > 200:
                logger.info("     %s: <%s 项>", key, len(val) if isinstance(val, list) else len(val))
            else:
                logger.info("     %s: %s", key, val)


def render_to_logger(report: ValidationReport, log: logging.Logger | None = None) -> None:
    target = log or logger
    _render_dataset_summary(report)
    _render_checks_overview(report)
    _render_failure_details(report)
    logger.info("=" * 60)
    logger.info(
        "overall=%s | exit_code=%d | duration=%.3fs | report=%s",
        report.overall_severity,
        report.exit_code,
        report.duration_seconds,
        report.report_path,
    )
