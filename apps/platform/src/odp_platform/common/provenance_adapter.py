# -*- coding: utf-8 -*-
"""将 D5 ProvenanceReport 适配为 config_log / TrainService 期望的 merger 接口。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from odp_platform.runtime_config.provenance import ProvenanceReport, ProvenanceStep

_SOURCE_LABELS = {
    "defaults": "DEFAULT",
    "yaml": "YAML",
    "cli": "CLI",
    "extra": "EXTRA",
}


def _label(source: str) -> str:
    return _SOURCE_LABELS.get(source, source.upper())


@dataclass(frozen=True)
class ProvenanceStepView:
    value: Any
    source_label: str


class FieldMetadataView:
    """兼容课程 ConfigMetadata 的只读视图。"""

    def __init__(self, steps: List[ProvenanceStep]) -> None:
        self._steps = steps

    @property
    def source_label(self) -> str:
        if not self._steps:
            return "未知"
        return _label(self._steps[-1].source)

    def chain(self) -> List[ProvenanceStepView]:
        return [
            ProvenanceStepView(step.value, _label(step.source))
            for step in reversed(self._steps)
        ]


class ProvenanceMergerAdapter:
    """供 config_log / 审计 JSON 使用的 merger 适配器。"""

    def __init__(self, provenance: ProvenanceReport) -> None:
        self.provenance = provenance

    def get_metadata(self, field_name: str) -> FieldMetadataView | None:
        steps = self.provenance.chains.get(field_name)
        if not steps:
            return None
        return FieldMetadataView(steps)

    def to_audit_log(self) -> Dict[str, Any]:
        return self.provenance.to_dict()
