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


def _infer_type(value: Any) -> str:
    """从默认值推断字段的 JSON 类型名。"""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    return "string"


def _field_spec_to_dict(spec: FieldSpec) -> dict[str, Any]:
    """将单个 FieldSpec 转为适合 LLM 消费的纯字典。"""
    entry: dict[str, Any] = {
        "name": spec.name,
        "type": _infer_type(spec.default),
        "default": spec.default,
        "description": spec.description,
        "group": spec.group,
    }
    if spec.choices:
        entry["choices"] = list(spec.choices)
    if spec.min_value is not None:
        entry["min_value"] = spec.min_value
    if spec.max_value is not None:
        entry["max_value"] = spec.max_value
    if spec.examples:
        entry["examples"] = list(spec.examples)
    if spec.tuning_tips:
        entry["tuning_tips"] = list(spec.tuning_tips)
    return entry


def get_all_field_specs(task_kind: str | None = None) -> dict[str, list[dict[str, Any]]]:
    """导出全部或指定任务的字段规格，用于外部消费（如 LLM prompt 注入）。

    Args:
        task_kind: 若为 None 则返回所有任务；否则只返回指定任务。

    Returns:
        {task_kind: [field_spec_dict, ...], ...}
    """
    from odp_platform.runtime_config.schemas import SCHEMAS

    tasks = [task_kind] if task_kind else list(SCHEMAS.keys())
    result: dict[str, list[dict[str, Any]]] = {}
    for tk in tasks:
        schema = SCHEMAS[tk]
        result[tk] = [_field_spec_to_dict(f) for f in schema.fields]
    return result
