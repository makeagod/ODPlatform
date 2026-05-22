#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""odp-config-gen — 生成运行配置 YAML 模板 (FR-19/UI-01)。"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from odp_platform.logging import setup_cli_logging
from odp_platform.common.paths import runtime_config_path
from odp_platform.runtime_config.template import generate_config_template

logger = logging.getLogger(__name__)

TASK_CHOICES = ("train", "val", "predict")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="odp-config-gen",
        description="根据代码 SSoT 生成带注释的运行配置 YAML 模板",
    )
    p.add_argument(
        "--task", "-t", required=True, choices=TASK_CHOICES,
        help="任务类型: train / val / predict",
    )
    p.add_argument(
        "--output", "-o", type=Path, default=None,
        help="输出路径（默认可 configs/runtime/<task>.yaml）",
    )
    p.add_argument(
        "--force", action="store_true",
        help="目标已存在时强制覆盖",
    )
    p.add_argument(
        "--no-backup", action="store_true",
        help="覆盖时不备份原文件",
    )
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    setup_cli_logging("config_gen")

    out = args.output or runtime_config_path(args.task)
    try:
        path = generate_config_template(
            args.task,
            out,
            force=args.force,
            backup=not args.no_backup,
        )
        if path.exists():
            logger.info("完成: %s", path)
        return 0
    except Exception:
        logger.exception("模板生成失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
