# -*- coding: utf-8 -*-
"""多来源合并 (FR-09)。"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from odp_platform.runtime_config.fields import TaskSchema
from odp_platform.runtime_config.provenance import ProvenanceReport


def merge_config(
    schema: TaskSchema,
    source_layers: List[Tuple[str, Dict[str, Any]]],
    provenance: ProvenanceReport,
) -> Dict[str, Any]:
    """
    source_layers: 从低优先级到高优先级排列，如 [("defaults", d0), ("yaml", d1), ("cli", d2)]
    """
    from odp_platform.runtime_config.exceptions import UnknownFieldError

    known = schema.known_names()
    merged = dict(schema.defaults_dict())
    for key, val in merged.items():
        provenance.record(key, "defaults", val)

    for source_name, layer in source_layers:
        if source_name == "defaults":
            continue
        for key, value in layer.items():
            if key not in known:
                raise UnknownFieldError(f"未知字段 {key!r}（来源: {source_name}）")
            merged[key] = value
            provenance.record(key, source_name, value)

    return merged
