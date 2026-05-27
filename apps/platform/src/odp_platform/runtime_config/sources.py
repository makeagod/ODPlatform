# -*- coding: utf-8 -*-
"""配置来源加载 (FR-05~07) — 委托 ``loaders`` 模块。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from odp_platform.common.paths import (
    CONFIGS_DIR,
    ROOT_DIR,
    RUNTIME_CONFIGS_DIR,
    runtime_config_path,
)
from odp_platform.runtime_config.exceptions import (
    ConfigFileNotFoundError,
    ConfigParseError,
)
from odp_platform.runtime_config.loaders import CLILoader, YAMLLoader, format_gen_cmd


def resolve_config_path(path: str | Path, task: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    if len(p.parts) == 1:
        stem = p.name if p.suffix else f"{task}.yaml"
        return runtime_config_path(stem)
    for base in (CONFIGS_DIR, RUNTIME_CONFIGS_DIR.parent, ROOT_DIR):
        candidate = (base / p).resolve()
        if candidate.exists():
            return candidate
    return (ROOT_DIR / p).resolve()


def load_yaml_source(path: Path, task: str) -> Dict[str, Any]:
    """加载 YAML 为 dict（平台异常类型）。"""
    loader = YAMLLoader(config_dir=RUNTIME_CONFIGS_DIR)
    try:
        return loader.load(path)
    except FileNotFoundError as exc:
        expected = Path(path).resolve()
        cmd = format_gen_cmd(task)
        raise ConfigFileNotFoundError(
            f"配置文件不存在: {expected}\n"
            f"不能静默继续。请执行:\n  {cmd}\n"
            f"或在 {RUNTIME_CONFIGS_DIR} 下放置该文件。"
        ) from exc
    except ValueError as exc:
        raise ConfigParseError(str(exc)) from exc


def load_cli_source(
    cli_overrides: Optional[Dict[str, Any]],
    reserved: frozenset[str] | None = None,
) -> Dict[str, Any]:
    """加载 CLI 覆盖为 dict。"""
    extra = list(reserved) if reserved else None
    return CLILoader(exclude=extra).load(cli_overrides)
