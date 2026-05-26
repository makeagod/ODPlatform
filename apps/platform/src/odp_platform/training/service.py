# -*- coding: utf-8 -*-
"""TrainService — 编排 D5 配置 + D4 校验 + D2 日志 + ultralytics 训练。"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ultralytics import YOLO

from odp_platform.common.config_log import log_effective_config, log_override_chains
from odp_platform.common.dataset_path import resolve_dataset_path
from odp_platform.common.log_rename import rename_log_to_save_dir
from odp_platform.common.model_path import resolve_model_path
from odp_platform.common.paths import RUNS_DIR, runtime_config_path
from odp_platform.common.result import TrainMetrics, log_train_metrics
from odp_platform.data_validation import render_to_logger, validate_dataset
from odp_platform.data_validation.registry import CheckSeverity
from odp_platform.runtime_config.train_build import build_train_config
from odp_platform.training.archive import archive_checkpoints

logger = logging.getLogger(__name__)


def _find_project_log_path() -> Path | None:
    import logging as _logging

    from odp_platform.logging.constants import ROOT_LOGGER_NAME

    root = _logging.getLogger(ROOT_LOGGER_NAME)
    for h in root.handlers:
        if isinstance(h, _logging.FileHandler):
            return Path(h.baseFilename)
    return None


@dataclass(frozen=True)
class TrainResult:
    success: bool
    output_dir: Path
    best_weight: Path | None = None
    last_weight: Path | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    train_time: float | None = None
    error: str | None = None
    audit_path: Path | None = None
    log_path: Path | None = None


class TrainService:
    """YOLO 训练流程编排。"""

    def train(
        self,
        yaml_path: str | Path | None = None,
        cli_args: dict[str, Any] | None = None,
        *,
        pre_validate: bool = True,
        archive: bool = True,
        rename_log: bool = True,
    ) -> TrainResult:
        start = datetime.now()
        output_dir: Path | None = None

        try:
            if yaml_path is None:
                yaml_path = runtime_config_path("train")

            config, merger = build_train_config(
                yaml_path=yaml_path,
                cli_args=cli_args,
            )

            logger.info("=" * 60)
            logger.info("开始 YOLO 训练 (task=%s)".center(60), config.task)
            logger.info("=" * 60)

            raw_model = config.model or "yolo11n.pt"
            raw_data = config.data
            logger.info("任务类型:    %s", config.task)
            logger.info("数据集(声明): %s", raw_data)
            data_path = resolve_dataset_path(raw_data or "")
            logger.info("数据集(解析): %s", data_path)
            logger.info("模型(声明):  %s", raw_model)
            model_path = resolve_model_path(raw_model)
            logger.info("模型(解析):  %s", model_path)

            log_effective_config(config, merger, logger=logger)
            log_override_chains(config, merger, logger=logger)

            if pre_validate:
                logger.info("=" * 60)
                logger.info("数据集预校验 (D4)".center(60))
                logger.info("=" * 60)
                report = validate_dataset(data_path, task_type=config.task)
                render_to_logger(report, log=logger)
                if report.exit_code >= 2:
                    error_count = sum(
                        1 for r in report.results if r.severity == CheckSeverity.ERROR
                    )
                    raise RuntimeError(
                        f"数据集校验失败 ({error_count} 个 ERROR)。"
                        f"请用 odp-validate --dataset {data_path.stem} "
                        f"--task {config.task} 修复后再训练；"
                        f"或加 --no-pre-validate（不推荐）。"
                    )

            model = YOLO(str(model_path))

            yolo_kwargs = config.to_ultralytics_kwargs()
            yolo_kwargs["data"] = str(data_path)
            yolo_kwargs.setdefault("project", str(RUNS_DIR / f"{config.task}_train"))

            logger.info("=" * 60)
            logger.info("启动训练".center(60))
            logger.info("=" * 60)
            logger.info("输出目录(project): %s", yolo_kwargs["project"])

            yolo_results = model.train(**yolo_kwargs)
            output_dir = Path(yolo_results.save_dir)

            logger.info("=" * 60)
            logger.info("训练完成".center(60))
            logger.info("=" * 60)
            metrics = TrainMetrics.from_yolo_results(
                yolo_results, model_trainer=getattr(model, "trainer", None)
            )
            log_train_metrics(metrics, logger=logger)

            model_stem = Path(raw_model).stem

            if rename_log:
                rename_log_to_save_dir(output_dir, model_stem)

            archived: dict[str, Path] = {}
            if archive:
                archived = archive_checkpoints(
                    train_dir=output_dir,
                    model_filename=raw_model,
                )

            audit_path = output_dir / "odp_audit.json"
            log_path = _find_project_log_path()
            try:
                audit_payload = {
                    "config": config.to_audit_snapshot(),
                    "merger": merger.to_audit_log(),
                    "metrics": metrics.to_dict(),
                    "result_summary": {
                        "best_archive": str(archived.get("best", "")) or None,
                        "last_archive": str(archived.get("last", "")) or None,
                        "train_time_sec": (datetime.now() - start).total_seconds(),
                        "log_path": str(log_path) if log_path else None,
                    },
                }
                audit_path.write_text(
                    json.dumps(audit_payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                logger.info("审计快照: %s", audit_path)
            except OSError as e:
                logger.warning("写审计快照失败(不影响训练结果): %s", e)
                audit_path = None

            train_time = (datetime.now() - start).total_seconds()
            best_weight = archived.get("best") or (output_dir / "weights" / "best.pt")
            last_weight = archived.get("last") or (output_dir / "weights" / "last.pt")

            logger.info("=" * 60)
            logger.info("训练总耗时: %.2f 秒", train_time)
            logger.info("输出目录:   %s", output_dir)
            logger.info("最佳权重:   %s", best_weight)
            if log_path:
                logger.info("本次日志:   %s", log_path)
            logger.info("=" * 60)

            return TrainResult(
                success=True,
                output_dir=output_dir,
                best_weight=best_weight if best_weight.exists() else None,
                last_weight=last_weight if last_weight.exists() else None,
                metrics=metrics.overall,
                train_time=train_time,
                audit_path=audit_path,
                log_path=log_path,
            )

        except Exception as e:
            logger.error("训练失败: %s", e, exc_info=True)
            train_time = (datetime.now() - start).total_seconds()
            return TrainResult(
                success=False,
                output_dir=output_dir or Path("unknown"),
                metrics={},
                train_time=train_time,
                error=str(e),
                log_path=_find_project_log_path(),
            )


def train_yolo(
    yaml_path: str | Path | None = None,
    cli_args: dict[str, Any] | None = None,
    *,
    pre_validate: bool = True,
    archive: bool = True,
    rename_log: bool = True,
) -> TrainResult:
    return TrainService().train(
        yaml_path=yaml_path,
        cli_args=cli_args,
        pre_validate=pre_validate,
        archive=archive,
        rename_log=rename_log,
    )
