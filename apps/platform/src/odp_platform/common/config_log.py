# -*- coding: utf-8 -*-
"""按字段维度打印配置生效值与来源链。"""
from __future__ import annotations

import logging
from typing import Any

from odp_platform.common.string_utils import pad_to_width


def log_effective_config(
    config: Any,
    merger: Any,
    *,
    logger: logging.Logger | None = None,
    key_width: int = 20,
    section_width: int = 60,
) -> None:
    log = logger or logging.getLogger(__name__)

    log.info("=" * section_width)
    log.info("配置参数信息".center(section_width))
    log.info("-" * section_width)

    for field_name in config.__class__.model_fields.keys():
        value = getattr(config, field_name, None)
        meta = _safe_get_metadata(merger, field_name)
        source_label = meta.source_label if meta is not None else "未知"
        log.info(
            f"{pad_to_width(field_name, key_width)}: {value}  "
            f"(来源: {source_label})"
        )


def log_override_chains(
    config: Any,
    merger: Any,
    *,
    logger: logging.Logger | None = None,
    key_width: int = 20,
    section_width: int = 60,
) -> None:
    log = logger or logging.getLogger(__name__)

    log.info("-" * section_width)
    log.info("配置覆盖情况".center(section_width))
    log.info("-" * section_width)

    for field_name in config.__class__.model_fields.keys():
        meta = _safe_get_metadata(merger, field_name)
        if meta is None:
            value = getattr(config, field_name, None)
            log.info(f"{pad_to_width(field_name, key_width)}: {value}")
            continue

        chain_str = " <- ".join(
            f"{m.value}({m.source_label})" for m in meta.chain()
        )
        log.info(f"{pad_to_width(field_name, key_width)}: {chain_str}")


def _safe_get_metadata(merger: Any, field_name: str) -> Any:
    if not hasattr(merger, "get_metadata"):
        return None
    try:
        return merger.get_metadata(field_name)
    except Exception:
        return None
