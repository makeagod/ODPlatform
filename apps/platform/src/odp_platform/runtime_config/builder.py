# -*- coding: utf-8 -*-
"""一站式配置构建 (FR-21)。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from odp_platform.runtime_config.config_object import RuntimeConfig
from odp_platform.runtime_config.merge import merge_config
from odp_platform.runtime_config.provenance import ProvenanceReport
from odp_platform.runtime_config.schemas import SCHEMAS
from odp_platform.runtime_config.sources import load_cli_source, load_yaml_source, resolve_config_path
from odp_platform.runtime_config.validate import validate_config


def build_config(
    task_kind: str,
    *,
    yaml_path: str | Path | None = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
    extra_layers: Optional[List[Tuple[str, Dict[str, Any]]]] = None,
    source_priority: Optional[List[str]] = None,
    preview_only: bool = False,
) -> RuntimeConfig:
    """
    加载 → 合并 → 验证 → 返回 RuntimeConfig + 溯源。

    默认优先级（低→高）: defaults < yaml < cli < extra
    """
    if task_kind not in SCHEMAS:
        raise ValueError(f"未知任务类型: {task_kind!r}")
    schema = SCHEMAS[task_kind]
    priority = source_priority or ["defaults", "yaml", "cli", "extra"]

    layers: Dict[str, Dict[str, Any]] = {}
    if yaml_path is not None:
        resolved = resolve_config_path(yaml_path, task_kind)
        layers["yaml"] = load_yaml_source(resolved, task_kind)
    if cli_overrides:
        layers["cli"] = load_cli_source(cli_overrides)
    if extra_layers:
        for name, data in extra_layers:
            layers[name] = data

    ordered: List[Tuple[str, Dict[str, Any]]] = [("defaults", schema.defaults_dict())]
    for name in priority:
        if name == "defaults":
            continue
        if name in layers:
            ordered.append((name, layers[name]))

    provenance = ProvenanceReport()
    merged = merge_config(schema, ordered, provenance)

    if preview_only:
        return RuntimeConfig(task_kind, merged, schema, provenance)

    warnings = tuple(validate_config(schema, merged, provenance))
    return RuntimeConfig(task_kind, merged, schema, provenance, warnings)


def build_train_config(**kwargs) -> RuntimeConfig:
    return build_config("train", **kwargs)


def build_val_config(**kwargs) -> RuntimeConfig:
    return build_config("val", **kwargs)


def build_predict_config(**kwargs) -> RuntimeConfig:
    return build_config("predict", **kwargs)
