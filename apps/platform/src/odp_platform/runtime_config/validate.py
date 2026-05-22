# -*- coding: utf-8 -*-
"""配置验证 (FR-12~14)。"""
from __future__ import annotations

import logging
from typing import Any, List, Optional, Tuple

from odp_platform.common.constants import Task
from odp_platform.runtime_config.exceptions import ConfigValidationError
from odp_platform.runtime_config.fields import TaskSchema
from odp_platform.runtime_config.provenance import ProvenanceReport
from odp_platform.runtime_config.schemas.train import TRAIN_WARN_VALIDATORS

logger = logging.getLogger(__name__)
USER_LOGGER = logging.getLogger("odp_platform.runtime_config.user")


def validate_config(
    schema: TaskSchema,
    values: dict[str, Any],
    provenance: ProvenanceReport,
    *,
    collect_warnings: bool = True,
) -> List[str]:
    warnings: List[str] = []
    fmap = schema.field_map()

    for name, spec in fmap.items():
        if name not in values:
            continue
        val = values[name]
        if name == "task" and val not in Task.all():
            chain = provenance.format_field(name)
            raise ConfigValidationError(
                f"task={val!r} 不在合法集合 {Task.all()}。\n"
                f"若要为实验命名，请使用 experiment_id 字段。\n溯源: {chain}"
            )
        err = spec.validate_value(val)
        if err:
            chain = provenance.format_field(name)
            raise ConfigValidationError(
                f"字段 {name}={val!r} 不合法: {err}\n溯源: {chain}"
            )

    for validator in schema.cross_field_validators:
        msg = validator(values)
        if msg:
            raise ConfigValidationError(msg)

    warn_validators = TRAIN_WARN_VALIDATORS if schema.task_kind == "train" else ()
    for validator in warn_validators:
        msg = validator(values)
        if msg and collect_warnings:
            warnings.append(msg)
            USER_LOGGER.warning(msg)
            logger.info("配置冗余警告: %s", msg)

    return warnings
