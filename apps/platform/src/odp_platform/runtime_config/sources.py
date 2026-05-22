# -*- coding: utf-8 -*-
"""配置来源加载 (FR-05~07)。"""
from __future__ import annotations

import locale
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from odp_platform.common.paths import ROOT_DIR, RUNTIME_CONFIGS_DIR, runtime_config_path
from odp_platform.runtime_config.exceptions import (
    ConfigFileNotFoundError,
    ConfigParseError,
)

logger = logging.getLogger(__name__)

_GEN_CMD = "odp-config-gen --task {task} --output {path}"


def resolve_config_path(path: str | Path, task: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    if len(p.parts) == 1:
        return runtime_config_path(task, p.name)
    for base in (RUNTIME_CONFIGS_DIR.parent, ROOT_DIR):
        candidate = (base / p).resolve()
        if candidate.exists():
            return candidate
    return (ROOT_DIR / p).resolve()


def load_yaml_source(path: Path, task: str) -> Dict[str, Any]:
    if not path.exists():
        expected = path.resolve()
        cmd = _GEN_CMD.format(task=task, path=expected)
        raise ConfigFileNotFoundError(
            f"配置文件不存在: {expected}\n"
            f"不能静默继续。请执行:\n  {cmd}\n"
            f"或在 {RUNTIME_CONFIGS_DIR} 下放置该文件。"
        )
    raw_bytes = path.read_bytes()
    text: Optional[str] = None
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        logger.warning("UTF-8 解码失败，尝试系统默认编码: %s", path)
        text = raw_bytes.decode(locale.getpreferredencoding(False), errors="replace")

    loaded = yaml.safe_load(text)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigParseError(f"YAML 顶层必须是 dict，实际为 {type(loaded).__name__}: {path}")
    return {k: v for k, v in loaded.items() if v is not None}


def load_cli_source(
    cli_overrides: Optional[Dict[str, Any]],
    reserved: frozenset[str] | None = None,
) -> Dict[str, Any]:
    if not cli_overrides:
        return {}
    reserved = reserved or frozenset()
    out: Dict[str, Any] = {}
    for key, val in cli_overrides.items():
        if key.startswith("_") or key in reserved:
            continue
        if val is None:
            continue
        out[key] = val
    return out
