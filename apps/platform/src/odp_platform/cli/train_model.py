# -*- coding: utf-8 -*-
"""odp-train CLI — argparse + 装配日志 + 调用 TrainService。

职责边界:
  - 解析 CLI → dict，交给 D5 build_train_config 合并
  - 唯一装配文件日志 handler 的入口（setup_cli_logging）
  - 调用 TrainService.train，翻译退出码 0/1/130

不做: 合并配置(D5)、数据集校验(D4)、ultralytics 调用(service)
"""
from __future__ import annotations

import argparse
import logging
import sys

from odp_platform.common.paths import runtime_config_path
from odp_platform.logging import setup_cli_logging
from odp_platform.training.service import TrainService

_NON_CONFIG_KEYS = frozenset({
    "yaml",
    "pre_validate",
    "archive",
    "rename_log",
    "academic_plots",
    "log_level",
})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odp-train",
        description="YOLO 训练 — D5 配置 + D4 校验 + ultralytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  odp-train
  odp-train --epochs 3 --batch 8 --device cpu --model yolov8n.pt --data rsod.yaml
  odp-train --epochs 3 --batch 8 --device 0 --model yolov8n.pt --data rsod.yaml
  odp-train --yaml configs/runtime/train.yaml --epochs 200
  odp-train --no-pre-validate
        """,
    )

    parser.add_argument(
        "--yaml",
        type=str,
        default=None,
        help="运行配置 YAML（默认 configs/runtime/train.yaml）",
    )

    parser.add_argument("--model", type=str, help="模型路径或文件名（如 yolov8n.pt）")
    parser.add_argument("--data", type=str, help="数据集 yaml 或名称（如 rsod / rsod.yaml）")
    parser.add_argument("--epochs", type=int, help="训练轮数")
    parser.add_argument("--batch", type=int, help="batch size（支持 -1）")
    parser.add_argument("--imgsz", type=int, help="输入图像尺寸")
    parser.add_argument("--device", type=str, help="设备：0 / cpu / 0,1")
    parser.add_argument("--lr0", type=float, help="初始学习率")
    parser.add_argument("--optimizer", type=str, help="优化器")
    parser.add_argument("--workers", type=int, help="DataLoader workers")
    parser.add_argument("--seed", type=int, help="随机种子")
    parser.add_argument("--project", type=str, help="输出根目录")
    parser.add_argument("--name", type=str, help="ultralytics 运行名")
    parser.add_argument(
        "--experiment-name",
        dest="experiment_name",
        type=str,
        help="实验名（平台目录用，映射 experiment_name）",
    )

    parser.add_argument(
        "--no-pre-validate",
        dest="pre_validate",
        action="store_false",
        default=True,
        help="跳过训练前 D4 数据集校验（不推荐）",
    )
    parser.add_argument(
        "--no-archive",
        dest="archive",
        action="store_false",
        default=True,
        help="不归档 best/last 到 models/checkpoints/",
    )
    parser.add_argument(
        "--no-rename-log",
        dest="rename_log",
        action="store_false",
        default=True,
        help="训练后不将日志文件改名为 <save_dir>_<ts>_<model>.log",
    )
    parser.add_argument(
        "--academic-plots",
        action="store_true",
        help="学术风格出图（预留，需 plot_style 模块）",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别",
    )
    return parser


def _setup_logging(log_level: str) -> None:
    setup_cli_logging("train", log_level=getattr(logging, log_level))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.academic_plots:
        logging.getLogger(__name__).debug(
            "academic-plots 已请求，plot_style 模块尚未接入，已忽略"
        )

    _setup_logging(args.log_level)
    log = logging.getLogger("odp_platform.cli.train_model")

    cli_args = {
        k: v for k, v in vars(args).items()
        if v is not None and k not in _NON_CONFIG_KEYS
    }

    yaml_path = args.yaml or runtime_config_path("train")
    log.info("启动 odp-train, YAML=%s, CLI 覆盖字段=%s", yaml_path, list(cli_args.keys()))

    try:
        result = TrainService().train(
            yaml_path=yaml_path,
            cli_args=cli_args,
            pre_validate=args.pre_validate,
            archive=args.archive,
            rename_log=args.rename_log,
        )
    except KeyboardInterrupt:
        log.warning("用户中断 (Ctrl+C)")
        return 130
    except Exception as e:
        log.error("未预期异常: %s", e, exc_info=True)
        return 1

    if result.success:
        log.info(
            "训练成功，用时 %.2fs，输出 %s",
            result.train_time or 0,
            result.output_dir,
        )
        return 0

    log.error("训练失败: %s", result.error)
    return 1


if __name__ == "__main__":
    sys.exit(main())
