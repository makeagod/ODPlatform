# -*- coding: utf-8 -*-
"""odp-validate CLI — 仅 parse / 调度 / 渲染 / 退出码。"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from odp_platform.common.logging_utils import get_logger
from odp_platform.common.paths import LOGGING_DIR, dataset_yaml_path
from odp_platform.data_validation.render import render_to_logger
from odp_platform.data_validation.service import validate_dataset

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ODPlatform 数据集质检 (data_validation)",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dataset", type=str, help="数据集名称 (configs/datasets/<name>.yaml)")
    group.add_argument("--yaml", type=Path, help="直接指定 YAML 路径")
    parser.add_argument(
        "--task",
        choices=("detect", "segment"),
        default=None,
        help="任务类型；默认从 yaml.task 读取，否则 detect",
    )
    parser.add_argument("--no-report", action="store_true", help="不写入 JSON 报告")
    parser.add_argument("-v", "--verbose", action="store_true", help="DEBUG 日志")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    level = logging.DEBUG if args.verbose else logging.INFO
    get_logger(base_path=LOGGING_DIR, log_type="data_validation", log_level=level)

    if args.dataset:
        yaml_path = dataset_yaml_path(args.dataset)
        if not yaml_path.exists():
            logger.error(
                "数据集配置不存在: %s\n"
                "请先准备 data/raw/%s/ 并运行:\n"
                "  odp-transform --dataset %s --format <pascal_voc|coco|yolo>",
                yaml_path,
                args.dataset,
                args.dataset,
            )
            sys.exit(2)
    else:
        yaml_path = args.yaml.resolve()
        if not yaml_path.exists():
            logger.error("YAML 不存在: %s", yaml_path)
            sys.exit(2)

    try:
        report = validate_dataset(
            yaml_path=yaml_path,
            task_type=args.task,
            write_report=not args.no_report,
        )
        render_to_logger(report)
        sys.exit(report.exit_code)
    except KeyboardInterrupt:
        logger.warning("用户中断 (KeyboardInterrupt)")
        sys.exit(3)
    except Exception:
        logger.exception("odp-validate 发生未预期错误")
        sys.exit(3)


if __name__ == "__main__":
    main()
