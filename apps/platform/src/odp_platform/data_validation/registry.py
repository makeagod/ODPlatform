# -*- coding: utf-8 -*-
"""data_validation 注册表 + 数据契约。

与 D3 data_pipeline/registry 同源模式，调度相反：
    - D3: 互斥分发（一次选一个 converter）
    - D4: 聚合执行（一次跑全部 check，收集结果）
"""
from __future__ import annotations

import importlib
import logging
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List

from odp_platform.data_validation.snapshot import DatasetSnapshot

logger = logging.getLogger(__name__)


class CheckSeverity:
    """ERROR > WARNING > INFO > PASS"""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    PASS = "PASS"

    _ORDER = {"PASS": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}

    @classmethod
    def rank(cls, level: str) -> int:
        return cls._ORDER.get(level, -1)


@dataclass
class CheckResult:
    name: str
    severity: str
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.severity in (CheckSeverity.PASS, CheckSeverity.INFO)


@dataclass
class CheckContext:
    """check 统一入参；扩展只加字段，不改各 check 函数签名。"""

    yaml_path: Path
    snapshot: DatasetSnapshot | None = None


CheckFunc = Callable[[CheckContext], CheckResult]


@dataclass(frozen=True)
class CheckEntry:
    name: str
    func: CheckFunc


_REGISTRY: Dict[str, CheckEntry] = {}
_INITIALIZED: bool = False


def check(name: str) -> Callable[[CheckFunc], CheckFunc]:
    """注册 check；装饰器直接 return func，不包装。"""

    def decorator(func: CheckFunc) -> CheckFunc:
        if name in _REGISTRY:
            raise ValueError(
                f"check '{name}' 重复注册 — 第二次出现在 {func.__module__}.{func.__name__}"
            )
        _REGISTRY[name] = CheckEntry(name=name, func=func)
        return func

    return decorator


def _ensure_initialized() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return
    _INITIALIZED = True

    from odp_platform.data_validation import checks

    for _, mod_name, _ in pkgutil.iter_modules(checks.__path__):
        if mod_name.startswith("_"):
            continue
        importlib.import_module(f"{checks.__name__}.{mod_name}")


def get_all_checks() -> List[CheckEntry]:
    """返回全部注册的 check（注册顺序）。供 service 调度。"""
    _ensure_initialized()
    return list(_REGISTRY.values())


def get_check(name: str) -> CheckEntry:
    _ensure_initialized()
    if name not in _REGISTRY:
        raise KeyError(f"check '{name}' 未注册 — 已注册的: {list(_REGISTRY)}")
    return _REGISTRY[name]


def list_check_names() -> List[str]:
    _ensure_initialized()
    return list(_REGISTRY.keys())


def iter_checks() -> List[CheckEntry]:
    """按名称排序返回（稳定输出顺序）。"""
    _ensure_initialized()
    return [_REGISTRY[k] for k in sorted(_REGISTRY.keys())]


def list_checks() -> List[str]:
    """list_check_names 的别名，兼容既有测试。"""
    return sorted(list_check_names())


# 兼容旧内部名
_ensure_checks_imported = _ensure_initialized
