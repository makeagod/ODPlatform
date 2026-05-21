# -*- coding: utf-8 -*-
"""D4 数据契约 + @check 注册表 + 自动发现。"""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from odp_platform.data_validation.snapshot import DatasetSnapshot

_CHECKS_IMPORTED = False


class CheckSeverity:
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    PASS = "PASS"

    _ORDER = (PASS, INFO, WARNING, ERROR)

    @classmethod
    def rank(cls, level: str) -> int:
        try:
            return cls._ORDER.index(level)
        except ValueError:
            return -1


@dataclass
class CheckResult:
    name: str
    severity: str
    summary: str
    details: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return self.severity in (CheckSeverity.PASS, CheckSeverity.INFO)


@dataclass
class CheckContext:
    yaml_path: Path
    snapshot: DatasetSnapshot


CheckFunc = Callable[[CheckContext], CheckResult]


@dataclass(frozen=True)
class CheckEntry:
    name: str
    func: CheckFunc


_REGISTRY: Dict[str, CheckEntry] = {}


def check(name: str) -> Callable[[CheckFunc], CheckFunc]:
    def decorator(func: CheckFunc) -> CheckFunc:
        if name in _REGISTRY:
            raise ValueError(f"check {name!r} 已注册，禁止重复注册")
        _REGISTRY[name] = CheckEntry(name=name, func=func)
        return func

    return decorator


def list_checks() -> List[str]:
    _ensure_checks_imported()
    return sorted(_REGISTRY.keys())


def get_check(name: str) -> CheckEntry:
    _ensure_checks_imported()
    if name not in _REGISTRY:
        raise KeyError(f"未注册的 check: {name!r}")
    return _REGISTRY[name]


def iter_checks() -> List[CheckEntry]:
    _ensure_checks_imported()
    return [_REGISTRY[k] for k in sorted(_REGISTRY.keys())]


def _ensure_checks_imported() -> None:
    global _CHECKS_IMPORTED
    if _CHECKS_IMPORTED:
        return
    from odp_platform.data_validation import checks

    for module_info in pkgutil.iter_modules(checks.__path__):
        if module_info.name.startswith("_"):
            continue
        importlib.import_module(f"{checks.__name__}.{module_info.name}")
    _CHECKS_IMPORTED = True
