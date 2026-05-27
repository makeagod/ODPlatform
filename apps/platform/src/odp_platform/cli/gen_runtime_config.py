# -*- coding: utf-8 -*-
"""odp-config-gen — 兼容旧版 ``--task`` 风格，委托 ``generator.main``。

主推命令: ``odp-gen-config train``（见 :mod:`odp_platform.runtime_config.generator`）。
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from odp_platform.common.paths import runtime_config_path
from odp_platform.logging import setup_cli_logging
from odp_platform.runtime_config.generator import main as generator_main

logger = logging.getLogger(__name__)

# --task predict → generator 子命令 infer（讲义命名）
_TASK_TO_CLI = {"train": "train", "val": "val", "predict": "infer", "infer": "infer"}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="odp-config-gen",
        description=(
            "生成运行配置 YAML 模板（兼容入口）。"
            "推荐改用: odp-gen-config train|val|infer"
        ),
    )
    p.add_argument(
        "--task", "-t", required=True,
        choices=sorted(_TASK_TO_CLI),
        help="任务类型: train / val / predict / infer",
    )
    p.add_argument(
        "--output", "-o", type=Path, default=None,
        help="输出路径（默认 configs/runtime/<task>.yaml）",
    )
    p.add_argument(
        "--force", action="store_true",
        help="目标已存在时强制覆盖（等同 odp-gen-config --overwrite）",
    )
    p.add_argument(
        "--no-backup", action="store_true",
        help="覆盖时不备份原文件",
    )
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    setup_cli_logging("config_gen")

    cli_name = _TASK_TO_CLI[args.task]
    out = args.output
    if out is None:
        # predict 任务默认仍写 predict.yaml，infer 写 infer.yaml
        stem = "predict" if args.task == "predict" else cli_name
        out = runtime_config_path(stem)

    gen_argv = [cli_name]
    if out is not None:
        gen_argv.extend(["-o", str(out)])
    if args.force:
        gen_argv.append("--overwrite")
    if args.no_backup:
        gen_argv.append("--no-backup")

    logger.info(
        "odp-config-gen 已委托 odp-gen-config（子命令 %s）", cli_name
    )
    return generator_main(gen_argv)


if __name__ == "__main__":
    sys.exit(main())
