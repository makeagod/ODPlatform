# -*- coding: utf-8 -*-
"""配置模板生成 (FR-16~18) — 分组 + 行内注释，提升可读性。"""
from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from odp_platform.runtime_config.fields import FieldSpec, TaskSchema
from odp_platform.runtime_config.schemas import SCHEMAS
from odp_platform.runtime_config.sources import load_yaml_source

logger = logging.getLogger(__name__)

_GROUP_ORDER = ("meta", "data", "model", "train", "val", "predict", "augment", "general")
_GROUP_TITLES = {
    "meta": "元信息（平台）",
    "data": "数据集",
    "model": "模型权重",
    "train": "训练超参",
    "val": "验证超参",
    "predict": "推理超参",
    "augment": "数据增强",
    "general": "其他",
}

_FAQ = """
# ---------------------------------------------------------------------------
# 常见问题
# ---------------------------------------------------------------------------
# Q: 这个文件是干什么的？
# A: 训练/验证/推理的运行参数。改完后用 build_train_config(yaml_path=...) 加载。
#
# Q: 参数最终以谁为准？
# A: 默认优先级 — 命令行 > 本 YAML > 代码默认值。
#
# Q: 文件丢了怎么办？
# A: 运行 odp-gen-config train 重新生成（加 --overwrite 会备份旧文件）。
"""


def _format_yaml_value(value) -> str:
    dumped = yaml.safe_dump(value, allow_unicode=True, default_flow_style=True)
    return dumped.strip().split("\n", 1)[0]


def _field_block(spec: FieldSpec) -> list[str]:
    lines = [f"# {spec.name}: {spec.description}"]
    if spec.examples:
        lines.append(f"#   常用值: {', '.join(spec.examples)}")
    for tip in spec.tuning_tips:
        lines.append(f"#   提示: {tip}")
    lines.append(f"{spec.name}: {_format_yaml_value(spec.default)}")
    return lines


def generate_template_content(schema: TaskSchema) -> str:
    header = [
        "---",
        f"# ODPlatform 运行配置 — {schema.task_kind}",
        f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "#",
        "# 使用方式:",
        "#   1. 按下方分组修改参数（★ 标记项建议优先填写）",
        "#   2. Python: build_train_config(yaml_path='configs/runtime/train.yaml')",
        "#   3. 数据集需先 odp-transform，质检 odp-validate --dataset <name>",
        "",
    ]

    groups: dict[str, list[FieldSpec]] = {}
    for spec in schema.fields:
        groups.setdefault(spec.group, []).append(spec)

    body: list[str] = []
    ordered_groups = [g for g in _GROUP_ORDER if g in groups]
    ordered_groups += sorted(g for g in groups if g not in _GROUP_ORDER)

    for group in ordered_groups:
        title = _GROUP_TITLES.get(group, group)
        body.append("")
        body.append("# " + "=" * 72)
        body.append(f"# {title}")
        body.append("# " + "=" * 72)
        for spec in groups[group]:
            star = "★ " if spec.name in ("data", "experiment_id", "model") else ""
            if star:
                body.append(f"# {star}{spec.name}")
            body.extend(_field_block(spec))
            body.append("")

    return "\n".join(header + body).rstrip() + "\n" + _FAQ


def generate_config_template(
    task_kind: str,
    output_path: Path,
    *,
    force: bool = False,
    backup: bool = True,
) -> Path:
    if task_kind not in SCHEMAS:
        raise ValueError(f"未知任务: {task_kind}")
    schema = SCHEMAS[task_kind]
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force:
        logger.info("跳过生成，文件已存在: %s（使用 --force 覆盖）", output_path)
        return output_path

    if output_path.exists() and force and backup:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = output_path.with_suffix(output_path.suffix + f".bak.{ts}")
        shutil.copy2(output_path, backup_path)
        logger.info("已备份原文件至: %s", backup_path)

    content = generate_template_content(schema)
    output_path.write_text(content, encoding="utf-8")

    load_yaml_source(output_path, task_kind)
    logger.info("模板已写入: %s", output_path)
    return output_path
