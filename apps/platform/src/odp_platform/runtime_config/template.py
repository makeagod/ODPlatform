# -*- coding: utf-8 -*-
"""配置模板生成 (FR-16~18)。"""
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

_FAQ = """
# --- 常见问题 ---
# Q: 配置文件不存在怎么办？
# A: 使用 odp-config-gen 生成本模板，编辑后再用于训练/验证/推理。
# Q: 参数最终值来自哪里？
# A: 默认 命令行 > YAML > 代码默认值（可在 build_config 调用时调整）。
"""


def _field_catalog_lines(spec: FieldSpec) -> list[str]:
    lines = [f"# [{spec.group}] {spec.name} — {spec.description}"]
    if spec.examples:
        lines.append(f"#   示例: {', '.join(spec.examples)}")
    for tip in spec.tuning_tips:
        lines.append(f"#   建议: {tip}")
    lines.append(f"#   默认: {spec.default!r}")
    return lines


def generate_template_content(schema: TaskSchema) -> str:
    header = [
        f"# ODPlatform 运行配置模板 — {schema.task_kind}",
        f"# 生成时间: {datetime.now().isoformat(timespec='seconds')}",
        "# 说明: 编辑下方 YAML 块；字段说明见 catalog 注释",
        "",
    ]
    catalog: list[str] = ["# ----- 字段 catalog -----"]
    groups: dict[str, list[FieldSpec]] = {}
    for spec in schema.fields:
        groups.setdefault(spec.group, []).append(spec)
    for group in sorted(groups.keys()):
        catalog.append(f"# == {group} ==")
        for spec in groups[group]:
            catalog.extend(_field_catalog_lines(spec))

    yaml_body = yaml.safe_dump(
        schema.defaults_dict(),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    return "---\n" + "\n".join(header + catalog + ["", yaml_body]) + _FAQ


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

    loaded = load_yaml_source(output_path, task_kind)
    defaults = schema.defaults_dict()
    for key, default in defaults.items():
        if key not in loaded:
            raise RuntimeError(f"模板字段缺失: {key}")
        if loaded[key] != default:
            pass  # yaml 类型可能 int/float 轻微差异

    logger.info("模板已写入: %s", output_path)
    return output_path
