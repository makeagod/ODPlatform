# -*- coding: utf-8 -*-
"""字段元数据 SSoT (FR-01/02)。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Sequence, Tuple


@dataclass(frozen=True)
class FieldSpec:
    name: str
    default: Any
    description: str
    group: str = "general"
    examples: Tuple[str, ...] = ()
    tuning_tips: Tuple[str, ...] = ()
    sensitive: bool = False
    internal: bool = False
    choices: Optional[Tuple[Any, ...]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    type_check: Optional[Callable[[Any], bool]] = None

    def validate_value(self, value: Any) -> Optional[str]:
        if self.choices is not None and value not in self.choices:
            return f"必须在 {self.choices} 之一"
        if isinstance(value, bool):
            pass
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if self.min_value is not None and value < self.min_value:
                return f"不得小于 {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return f"不得大于 {self.max_value}"
        if self.type_check and not self.type_check(value):
            return "类型或格式不合法"
        if self.name == "batch" and isinstance(value, int) and value == 0:
            return "batch 不能为 0（可用 -1 表示自动）"
        return None


@dataclass(frozen=True)
class TaskSchema:
    task_kind: str
    fields: Tuple[FieldSpec, ...]
    internal_fields: frozenset[str] = frozenset()
    cross_field_validators: Tuple[Callable[[dict[str, Any]], Optional[str]], ...] = ()

    def field_map(self) -> dict[str, FieldSpec]:
        return {f.name: f for f in self.fields}

    def defaults_dict(self) -> dict[str, Any]:
        return {f.name: f.default for f in self.fields}

    def known_names(self) -> frozenset[str]:
        return frozenset(f.name for f in self.fields)
