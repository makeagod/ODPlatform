"""data_pipeline 注册表 + 统一参数包 + 能力声明。"""
from __future__ import annotations

import importlib
import logging
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from odp_platform.common.constants import Task

logger = logging.getLogger(__name__)


@dataclass
class ConvertOptions:
    """所有 converter 共用的参数包。"""
    task: str = Task.DETECT
    classes: Optional[List[str]] = None
    coco_cls91to80: bool = False
    random_state: int = 42


ConverterFunc = Callable[[Path, Path, ConvertOptions], List[str]]


@dataclass(frozen=True)
class ConverterEntry:
    func: ConverterFunc
    supported_tasks: Tuple[str, ...]

    def supports(self, task: str) -> bool:
        return task in self.supported_tasks


_REGISTRY: Dict[str, ConverterEntry] = {}


def register(
    format_name: str,
    supported_tasks: Tuple[str, ...] = (Task.DETECT,),
) -> Callable[[ConverterFunc], ConverterFunc]:
    def decorator(func: ConverterFunc) -> ConverterFunc:
        if format_name in _REGISTRY:
            logger.warning(f"格式 {format_name} 被重复注册, 后者覆盖前者")
        _REGISTRY[format_name] = ConverterEntry(
            func=func,
            supported_tasks=tuple(supported_tasks),
        )
        return func
    return decorator


def get_converter(format_name: str) -> ConverterEntry:
    _lazy_init()
    key = format_name.lower()
    if key not in _REGISTRY:
        raise ValueError(
            f"未注册的格式: {format_name!r}。已注册: {sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[key]


def list_capabilities() -> Dict[str, Tuple[str, ...]]:
    _lazy_init()
    return {fmt: entry.supported_tasks for fmt, entry in _REGISTRY.items()}


_LAZY_INITIALIZED = False


def _lazy_init() -> None:
    global _LAZY_INITIALIZED
    if _LAZY_INITIALIZED:
        return

    from odp_platform.data_pipeline import core

    for module_info in pkgutil.iter_modules(core.__path__):
        if module_info.name.startswith("_"):
            continue
        importlib.import_module(f"{core.__name__}.{module_info.name}")

    _LAZY_INITIALIZED = True
