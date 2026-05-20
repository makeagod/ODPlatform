# -*- coding: utf-8 -*-
"""
阶段 9: odp-transform 命令行 CLI 交互入口 (终极防御版)
"""
import argparse
import sys
from pathlib import Path

from odp_platform.common.logging_utils import get_logger
from odp_platform.data_pipeline import (
    DataPipelineOrchestrator,
    get_pipeline_capabilities,
    ConvertOptions,
)

logger = get_logger("odp-transform")


class SafeHelpFormatter(argparse.RawTextHelpFormatter):
    """
    🛠️ 终极防御型格式化器：
    重写底层拓展机制，强制让 argparse 放弃对所有文本进行 % 占位符格式化，
    彻底杜绝 ValueError: unsupported format character 崩溃。
    """
    def _expand_help(self, action):
        if action.help:
            # 强行将单百分号转义，防止底层执行 % params 报错
            return action.help.replace('%', '%%')
        return super()._expand_help(action)


def _format_capability_matrix() -> str:
    """实时将注册表中的格式和能力格式化输出，用于追加到 help 帮助文档末尾"""
    capabilities = get_pipeline_capabilities()
    matrix_str = "\n=========================================\n"
    matrix_str += "  当前平台支持的数据格式与能力矩阵:\n"
    matrix_str += "-----------------------------------------\n"
    for fmt, tasks in capabilities.items():
        tasks_joined = ", ".join(tasks)
        matrix_str += f"  - {fmt:<12} -> 支持任务: [{tasks_joined}]\n"
    matrix_str += "========================================="
    return matrix_str


def main():
    # 1. 创建使用终极安全格式化器的 ArgumentParser
    parser = argparse.ArgumentParser(
        description="ODPlatform 数据转换与智能切分流水线工具",
        formatter_class=SafeHelpFormatter,  # 👈 挂载我们的黄金防弹盾牌
        epilog=_format_capability_matrix()
    )

    # 2. 注入命令行参数规范
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="待转换的原始数据集名称（必须存放在 data/raw/<名字> 下）"
    )
    parser.add_argument(
        "--format",
        type=str,
        required=True,
        help="原始数据集的标注格式（例如: pascal_voc, coco, yolo）"
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="训练集切分比例 [默认: 0.8, 与课程 rsod.yaml 一致]"
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.1,
        help="验证集切分比例 [默认: 0.1]"
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.1,
        help="测试集切分比例 [默认: 0.1]"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="随机种子，确保切分结果100复现 [默认: 42]"
    )

    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info(f"[START] 数据准备流水线 | 数据集: {args.dataset}")
    logger.info("=" * 50)

    try:
        options = ConvertOptions(random_state=args.seed)
        orchestrator = DataPipelineOrchestrator(
            dataset_name=args.dataset,
            raw_format=args.format,
            options=options
        )

        yaml_path = orchestrator.run_pipeline(
            train_ratio=args.train_ratio,
            val_ratio=args.val_ratio,
            test_ratio=args.test_ratio
        )

        logger.info("=" * 50)
        logger.info("[OK] 流水线完成，数据处理成功")
        logger.info(f"[OK] YOLO 数据集: data/processed/{args.dataset}/")
        logger.info(f"[OK] 训练配置 YAML: {yaml_path}")
        logger.info("=" * 50)
        sys.exit(0)

    except ValueError as ve:
        logger.error(f"[FAIL] 业务逻辑或合规检查未通过: {ve}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"[FAIL] 流水线执行期间发生致命错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()