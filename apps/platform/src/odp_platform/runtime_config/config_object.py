# -*- coding: utf-8 -*-
"""已验证配置对象 (FR-20~22)。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from odp_platform.runtime_config.fields import TaskSchema
from odp_platform.runtime_config.provenance import ProvenanceReport


@dataclass
class RuntimeConfig:
    task_kind: str
    values: Dict[str, Any]
    schema: TaskSchema
    provenance: ProvenanceReport
    warnings: tuple[str, ...] = ()

    def get(self, name: str, default: Any = None) -> Any:
        return self.values.get(name, default)

    def to_yolo_config(self) -> "BaseConfig":
        """构建 Pydantic YOLO 配置（完整校验 + to_ultralytics_kwargs）。"""
        from odp_platform.runtime_config.base import BaseConfig
        from odp_platform.runtime_config.loader import build_yolo_config

        return build_yolo_config(self.task_kind, self.values)

    def to_backend_kwargs(self, backend_type: str = "ultralytics") -> Dict[str, Any]:
        """通过适配器将配置翻译为目标框架的原生参数字典。

        Args:
            backend_type: 后端标识，如 ``"ultralytics"`` / ``"mmdetection"``。
                          可通过 ``register_adapter()`` 扩展。
        """
        from odp_platform.runtime_config.adapters import get_adapter

        adapter = get_adapter(backend_type)
        return adapter.translate(self)

    def snapshot(self) -> Dict[str, Any]:
        return {"task_kind": self.task_kind, "values": dict(self.values)}

    @classmethod
    def from_snapshot(cls, payload: Dict[str, Any], schema: TaskSchema) -> "RuntimeConfig":
        from odp_platform.runtime_config.provenance import ProvenanceReport

        return cls(
            task_kind=payload["task_kind"],
            values=dict(payload["values"]),
            schema=schema,
            provenance=ProvenanceReport(),
        )

    def sensitive_fields(self) -> frozenset[str]:
        return frozenset(f.name for f in self.schema.fields if f.sensitive)
