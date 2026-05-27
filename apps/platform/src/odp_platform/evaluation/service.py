# -*- coding: utf-8 -*-
"""ValService — 编排 D5 配置 + D4 校验 + D2 日志 + ultralytics 验证。

D6 TrainService 的对偶：评估产物由 ultralytics 写入 runs/<task>_val/val<N>/，
不在 evaluation/ 下做 archive（见课程「撞墙②: 对称强迫症」）。
"""
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
from odp_platform.common.paths import CHECKPOINTS_DIR, PRETRAINED_MODELS_DIR, RUNS_DIR
from odp_platform.common.result import TrainMetrics, log_train_metrics
from odp_platform.data_validation import render_to_logger, validate_dataset
from odp_platform.data_validation.registry import CheckSeverity
from odp_platform.runtime_config.val_build import build_val_config

logger = logging.getLogger(__name__)

ValMetrics = TrainMetrics


def _find_project_log_path() -> Path | None:
    import logging as _logging

    from odp_platform.logging.constants import ROOT_LOGGER_NAME

    root = _logging.getLogger(ROOT_LOGGER_NAME)
    for h in root.handlers:
        if isinstance(h, _logging.FileHandler):
            return Path(h.baseFilename)
    return None


@dataclass(frozen=True)
class ValResult:
    """验证结果快照（无 best/last 权重，评估不归档）。"""

    success: bool
    output_dir: Path
    metrics: dict[str, float] = field(default_factory=dict)
    val_time: float | None = None
    error: str | None = None
    audit_path: Path | None = None
    log_path: Path | None = None


class ValService:
    """YOLO 验证流程编排。"""

    def evaluate(
        self,
        yaml_path: str | Path | None = None,
        cli_args: dict[str, Any] | None = None,
        *,
        pre_validate: bool = True,
        rename_log: bool = True,
    ) -> ValResult:
        start = datetime.now()
        output_dir: Path | None = None

        try:
            config, merger = build_val_config(
                yaml_path=yaml_path,
                cli_args=cli_args,
            )

            logger.info("=" * 60)
            logger.info("开始 YOLO 验证 (task=%s)".center(60), config.task)
            logger.info("=" * 60)

            raw_model = config.model
            raw_data = config.data

            if not raw_model:
                raise ValueError(
                    "验证必须指定模型 (config.model)。通常是 D6 归档过的权重，例如：\n"
                    "  odp-val --model train3-20260524-103045-yolo11n-best.pt\n"
                    "或在 val.yaml 里写 model: train3-...-best.pt"
                )
            if not raw_data:
                raise ValueError(
                    "验证必须指定数据集 (config.data)。例如：\n"
                    "  odp-val --data rsod.yaml\n"
                    "或在 val.yaml 里写 data: rsod.yaml\n"
                    "（若 val.yaml 尚未生成，先跑: odp-gen-config val）"
                )

            logger.info("任务类型:    %s", config.task)
            logger.info("数据集(声明): %s", raw_data)
            data_path = resolve_dataset_path(raw_data)
            logger.info("数据集(解析): %s", data_path)
            logger.info("模型(声明):  %s", raw_model)
            model_path = resolve_model_path(
                raw_model,
                search_dirs=[CHECKPOINTS_DIR, PRETRAINED_MODELS_DIR],
            )
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
                        f"数据集校验失败 ({error_count} 个 ERROR 级问题)。"
                        f"请用 `odp-validate --dataset {data_path.stem} "
                        f"--task {config.task}` 修复后再验证；"
                        f"或加 --no-pre-validate（不推荐）。"
                    )

            model = YOLO(str(model_path))

            yolo_kwargs = config.to_ultralytics_kwargs()
            yolo_kwargs["data"] = str(data_path)
            yolo_kwargs.setdefault("project", str(RUNS_DIR / f"{config.task}_val"))

            logger.info("=" * 60)
            logger.info("启动验证".center(60))
            logger.info("=" * 60)
            logger.info("输出目录(project): %s", yolo_kwargs["project"])

            yolo_results = model.val(**yolo_kwargs)
            output_dir = self._extract_save_dir(yolo_results, model)

            logger.info("=" * 60)
            logger.info("验证完成".center(60))
            logger.info("=" * 60)
            metrics = ValMetrics.from_yolo_results(
                yolo_results, model_trainer=getattr(model, "validator", None)
            )
            log_train_metrics(metrics, logger=logger)

            model_stem = Path(raw_model).stem

            if rename_log:
                rename_log_to_save_dir(output_dir, model_stem)

            audit_path = output_dir / "odp_audit.json"
            log_path = _find_project_log_path()
            try:
                audit_payload = {
                    "kind": "val",
                    "config": config.to_audit_snapshot(),
                    "merger": merger.to_audit_log(),
                    "metrics": metrics.to_dict(),
                    "result_summary": {
                        "val_time_sec": (datetime.now() - start).total_seconds(),
                        "log_path": str(log_path) if log_path else None,
                    },
                }
                audit_path.write_text(
                    json.dumps(audit_payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                logger.info("审计快照: %s", audit_path)
            except OSError as e:
                logger.warning("写审计快照失败(不影响验证结果): %s", e)
                audit_path = None

            val_time = (datetime.now() - start).total_seconds()

            logger.info("=" * 60)
            logger.info("验证总耗时: %.2f 秒", val_time)
            logger.info("输出目录:   %s", output_dir)
            if log_path:
                logger.info("本次日志:   %s", log_path)
            logger.info("=" * 60)

            return ValResult(
                success=True,
                output_dir=output_dir,
                metrics=metrics.overall,
                val_time=val_time,
                audit_path=audit_path,
                log_path=log_path,
            )

        except Exception as e:
            logger.error("验证失败: %s", e, exc_info=True)
            val_time = (datetime.now() - start).total_seconds()
            return ValResult(
                success=False,
                output_dir=output_dir or Path("unknown"),
                metrics={},
                val_time=val_time,
                error=str(e),
                log_path=_find_project_log_path(),
            )

    @staticmethod
    def _extract_save_dir(yolo_results: Any, model: Any) -> Path:
        save_dir = getattr(yolo_results, "save_dir", None)
        if save_dir is not None:
            return Path(save_dir)
        validator = getattr(model, "validator", None)
        if validator is not None:
            save_dir = getattr(validator, "save_dir", None)
            if save_dir is not None:
                return Path(save_dir)
        logger.warning(
            "无法从 ultralytics 提取 save_dir，走 'unknown' 兜底。日志改名可能跳过。"
        )
        return Path("unknown")


def evaluate_yolo(
    yaml_path: str | Path | None = None,
    cli_args: dict[str, Any] | None = None,
    *,
    pre_validate: bool = True,
    rename_log: bool = True,
) -> ValResult:
    return ValService().evaluate(
        yaml_path=yaml_path,
        cli_args=cli_args,
        pre_validate=pre_validate,
        rename_log=rename_log,
    )


def val_yolo(
    yaml_path: str | Path | None = None,
    cli_args: dict[str, Any] | None = None,
    *,
    pre_validate: bool = True,
    rename_log: bool = True,
) -> ValResult:
    """兼容旧 API（同 evaluate_yolo）。"""
    return evaluate_yolo(
        yaml_path=yaml_path,
        cli_args=cli_args,
        pre_validate=pre_validate,
        rename_log=rename_log,
    )
