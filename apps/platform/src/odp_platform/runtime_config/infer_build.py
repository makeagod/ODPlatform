# -*- coding: utf-8 -*-
"""D8 推理服务用的 build_infer_config(config, merger) 接口。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from odp_platform.common.paths import runtime_config_path
from odp_platform.common.provenance_adapter import ProvenanceMergerAdapter
from odp_platform.runtime_config.infer import YOLOInferConfig
from odp_platform.runtime_config.loaders import CLILoader, YAMLLoader, drop_none_values


def _merge_infer_dict(
    yaml_path: Union[str, Path, None],
    cli_args: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """合并 infer YAML + CLI → 扁平 dict（走 Pydantic 全字段校验）。"""
    merged: Dict[str, Any] = {}
    if yaml_path is not None:
        path = Path(yaml_path)
        if path.exists():
            merged.update(YAMLLoader().load(path))
    if cli_args:
        merged.update(CLILoader().load(cli_args))
    return drop_none_values(merged)


def build_infer_config(
    yaml_path: Union[str, Path, None] = None,
    cli_args: Optional[Dict[str, Any]] = None,
) -> Tuple[YOLOInferConfig, ProvenanceMergerAdapter]:
    """加载 infer 配置并返回 Pydantic 模型 + 溯源适配器（课程 D8 API）。

    推理字段多于 ``schemas/predict`` 的 FieldSpec 子集，因此 YAML/CLI
    直接合并后 ``YOLOInferConfig.model_validate``，溯源适配器对 CLI 覆盖字段做记录。
    """
    if yaml_path is None:
        yaml_path = runtime_config_path("infer")

    merged = _merge_infer_dict(yaml_path, cli_args)
    config = YOLOInferConfig.model_validate(merged)

    from odp_platform.runtime_config.provenance import ProvenanceReport

    provenance = ProvenanceReport()
    for key, value in config.model_dump().items():
        provenance.record(key, "merged", value)
    if cli_args:
        for key, value in drop_none_values(CLILoader().load(cli_args)).items():
            provenance.record(key, "cli", value)

    return config, ProvenanceMergerAdapter(provenance)
