# -*- coding: utf-8 -*-
"""odp-val — YOLO 模型验证命令行入口。

CLI 层只做三件事（跟 D6 odp-train 同款）：
  1. 解析 argparse
  2. 调 D2 setup_cli_logging 装 handler
  3. 调 ValService().evaluate()，按 ValResult.success 决定退出码
"""
from __future__ import annotations

import argparse
import logging
import sys

from odp_platform.common.paths import runtime_config_path
from odp_platform.evaluation.service import ValService
from odp_platform.logging import setup_cli_logging

_CONFIG_KEYS = frozenset({
    "model", "data", "imgsz", "batch", "device", "split",
    "conf", "iou", "max_det", "workers", "project", "name",
    "experiment_name", "half", "plots", "save_json",
})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odp-val",
        description="验证一个训练好的 YOLO 模型 (ODPlatform evaluation 子系统)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  odp-val --model train3-20260524-103045-yolo11n-best.pt --data rsod.yaml\n"
            "  odp-val --model yolo26m.pt --data rsod.yaml --device cpu\n"
            "  odp-val --yaml my_val.yaml\n"
            "  odp-val --no-pre-validate          # 跳过 D4 数据集校验(不推荐)\n"
            "\n"
            "提示: 若 val.yaml 还没生成, 先跑 `odp-gen-config val`."
        ),
    )

    parser.add_argument(
        "--yaml", dest="yaml_path", type=str, default=None,
        help="验证配置 YAML 路径(默认 configs/runtime/val.yaml)",
    )

    parser.add_argument(
        "--model", type=str,
        help="待验证的模型权重 —— 通常是 D6 归档的 best.pt 或 models/pretrained/ 下的权重",
    )
    parser.add_argument("--data", type=str, help="数据集 yaml —— D3 立的, 如 rsod.yaml")
    parser.add_argument("--imgsz", type=int, help="验证图像尺寸")
    parser.add_argument("--batch", type=int, help="验证 batch size")
    parser.add_argument("--device", type=str, help="设备, 如 0 / 0,1 / cpu")
    parser.add_argument("--split", type=str, help="用哪个划分验证: val / test / train")
    parser.add_argument("--conf", type=float, help="置信度阈值")
    parser.add_argument("--iou", type=float, help="NMS IoU 阈值")
    parser.add_argument("--max-det", dest="max_det", type=int, help="每张图最大检测数")
    parser.add_argument("--workers", type=int, help="DataLoader workers")
    parser.add_argument("--project", type=str, help="输出根目录")
    parser.add_argument("--name", type=str, help="ultralytics 运行名")
    parser.add_argument(
        "--experiment-name", dest="experiment_name", type=str,
        help="实验名（平台目录用）",
    )
    parser.add_argument(
        "--half",
        type=lambda x: x.lower() == "true",
        default=None,
        help="半精度推理 (true/false)",
    )
    parser.add_argument(
        "--plots",
        type=lambda x: x.lower() == "true",
        default=None,
        help="生成评估图表 (true/false)",
    )
    parser.add_argument(
        "--save-json", dest="save_json",
        type=lambda x: x.lower() == "true",
        default=None,
        help="保存 COCO JSON (true/false)",
    )

    parser.add_argument(
        "--no-pre-validate", dest="pre_validate",
        action="store_false",
        help="跳过验证前的 D4 数据集校验(不推荐)",
    )
    parser.add_argument(
        "--no-rename-log", dest="rename_log",
        action="store_false",
        help="不把日志文件名改成 <save_dir>_<ts>_<model>.log 形式",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别",
    )
    parser.set_defaults(pre_validate=True, rename_log=True)

    return parser


def main() -> int:
    args = build_parser().parse_args()

    setup_cli_logging("val", log_level=getattr(logging, args.log_level))

    cli_args = {
        k: v for k, v in vars(args).items()
        if k in _CONFIG_KEYS and v is not None
    }

    yaml_path = args.yaml_path or runtime_config_path("val")

    try:
        result = ValService().evaluate(
            yaml_path=yaml_path,
            cli_args=cli_args,
            pre_validate=args.pre_validate,
            rename_log=args.rename_log,
        )
    except KeyboardInterrupt:
        print("\n用户中断验证.", file=sys.stderr)
        return 130

    if result.success:
        print(f"验证完成, 输出目录: {result.output_dir}")
        if result.metrics:
            fitness = result.metrics.get("fitness")
            if fitness is not None:
                print(f"   fitness: {fitness:.4f}")
        return 0

    print(f"验证失败: {result.error}", file=sys.stderr)
    if result.log_path:
        print(f"   详见日志: {result.log_path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
