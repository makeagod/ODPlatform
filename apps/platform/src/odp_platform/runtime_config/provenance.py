# -*- coding: utf-8 -*-
"""配置溯源 (FR-10/11)。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ProvenanceStep:
    source: str
    value: Any


@dataclass
class ProvenanceReport:
    chains: Dict[str, List[ProvenanceStep]] = field(default_factory=dict)

    def record(self, field_name: str, source: str, value: Any) -> None:
        if field_name not in self.chains:
            self.chains[field_name] = []
        self.chains[field_name].append(ProvenanceStep(source=source, value=value))

    def current_source(self, field_name: str) -> str:
        chain = self.chains.get(field_name, [])
        return chain[-1].source if chain else "defaults"

    def format_field(self, field_name: str, mask_sensitive: bool = False) -> str:
        chain = self.chains.get(field_name, [])
        if not chain:
            return f"{field_name}: (no chain)"
        parts = [f"{s.source}={s.value!r}" for s in chain]
        return f"{field_name}: " + " -> ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            name: [{"source": s.source, "value": s.value} for s in steps]
            for name, steps in self.chains.items()
        }

    def human_readable(self, sensitive_fields: frozenset[str] | None = None) -> str:
        sensitive_fields = sensitive_fields or frozenset()
        lines = []
        for name in sorted(self.chains.keys()):
            if name in sensitive_fields:
                lines.append(f"{name}: <redacted>")
            else:
                lines.append(self.format_field(name))
        return "\n".join(lines)
