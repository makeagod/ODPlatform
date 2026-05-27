# -*- coding: utf-8 -*-
"""ConfigGenerator + ``odp-gen-config`` / ``python -m`` 入口（课程 D5 对齐）。

实现委托 :mod:`template.generate_config_template`；本模块提供讲义约定的
子命令风格 CLI 与 ``ConfigGenerator`` 类名。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Mapping

from odp_platform.common.paths import runtime_config_path
from odp_platform.runtime_config.template import generate_config_template

# CLI 子命令名 → (内部 schema task_kind, 人类可读标题)
CONFIG_CLASS_MAP: Mapping[str, tuple[str, str]] = {
    "train": ("train", "YOLO 训练配置"),
    "val": ("val", "YOLO 验证配置"),
    "infer": ("predict", "YOLO 推理配置"),
}


def cli_name_to_task_kind(name: str) -> str:
    """``train`` / ``val`` / ``infer`` → schema 键（infer → predict）。"""
    if name not in CONFIG_CLASS_MAP:
        raise ValueError(
            f"未知配置名: {name!r}，可选: {sorted(CONFIG_CLASS_MAP)}"
        )
    return CONFIG_CLASS_MAP[name][0]


def default_output_path(cli_name: str) -> Path:
    """默认输出路径：``configs/runtime/<cli_name>.yaml``（含 infer.yaml）。"""
    return runtime_config_path(cli_name)


class ConfigGenerator:
    """反射式 YAML 模板生成器（薄包装 ``generate_config_template``）。"""

    def generate(
        self,
        cli_name: str,
        output_path: Path,
        *,
        overwrite: bool = False,
        backup: bool = True,
        title: str | None = None,
    ) -> bool:
        """生成模板。

        Returns:
            True 表示已写入；False 表示文件已存在且未覆盖。
        """
        _ = title  # 保留 API，标题由 template 内 schema 决定
        task_kind = cli_name_to_task_kind(cli_name)
        existed = output_path.exists()
        generate_config_template(
            task_kind,
            output_path,
            force=overwrite,
            backup=backup,
        )
        if existed and not overwrite:
            return False
        return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odp-gen-config",
        description="从配置 SSoT 反射生成 YOLO 运行配置 YAML 模板",
    )
    parser.add_argument(
        "name",
        choices=sorted(CONFIG_CLASS_MAP),
        help="要生成的配置名 (train / val / infer)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="输出路径 (默认: configs/runtime/<name>.yaml)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已有文件 (默认不覆盖, 保护用户编辑过的 yaml)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="覆盖时不备份原文件 (默认会备份成 <name>.yaml.bak.<时间戳>)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """``odp-gen-config <name>`` 与 ``python -m odp_platform.runtime_config.generator``。"""
    args = build_parser().parse_args(argv)
    output_path = args.output or default_output_path(args.name)

    existed_before = output_path.exists()
    gen = ConfigGenerator()
    generated = gen.generate(
        args.name,
        output_path,
        overwrite=args.overwrite,
        backup=not args.no_backup,
    )

    if generated and (args.overwrite or not existed_before):
        print(f"已生成: {output_path}")
        return 0

    print(
        f"- 文件已存在, 未覆盖 (避免覆盖你已编辑的配置).\n"
        f"  路径: {output_path}\n"
        f"  如需重新生成, 加 --overwrite (覆盖前会自动备份)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
