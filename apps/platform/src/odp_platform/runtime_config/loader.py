# -*- coding: utf-8 -*-
"""Pydantic 配置类加载与 YAML 字段别名归一化。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Type, Union

from pydantic import BaseModel, ValidationError

from odp_platform.common.paths import runtime_config_path
from odp_platform.runtime_config.base import BaseConfig
from odp_platform.runtime_config.infer import YOLOInferConfig
from odp_platform.runtime_config.train import YOLOTrainConfig
from odp_platform.runtime_config.val import YOLOValConfig

YOLO_CONFIG_CLASSES: Dict[str, Type[BaseConfig]] = {
    "train": YOLOTrainConfig,
    "val": YOLOValConfig,
    "predict": YOLOInferConfig,
    "infer": YOLOInferConfig,
}

# 对外统一别名（与 predict 任务名一致）
YOLOPredictConfig = YOLOInferConfig


def normalize_for_pydantic(values: Dict[str, Any]) -> Dict[str, Any]:
    """将 FieldSpec/YAML 命名映射到 Pydantic 模型字段。"""
    out = dict(values)

    if "experiment_id" in out:
        eid = out.pop("experiment_id")
        if eid not in (None, "") and not out.get("experiment_name"):
            out["experiment_name"] = eid
    if "experiment_name" in out and out["experiment_name"] in (None, ""):
        out.pop("experiment_name", None)

    for key in ("data", "model", "project", "device"):
        if out.get(key) == "":
            out[key] = None

    return out


def build_yolo_config(task_kind: str, values: Dict[str, Any]) -> BaseConfig:
    """由合并后的扁平 dict 构建并校验 YOLO Pydantic 配置。"""
    if task_kind not in YOLO_CONFIG_CLASSES:
        raise ValueError(
            f"未知任务类型: {task_kind!r}，可选: {sorted(YOLO_CONFIG_CLASSES)}"
        )
    cls = YOLO_CONFIG_CLASSES[task_kind]
    try:
        return cls.model_validate(normalize_for_pydantic(values))
    except ValidationError as exc:
        raise exc


def load_yolo_config_from_yaml(
    name: str,
    *,
    task_kind: str | None = None,
    path: Path | None = None,
) -> BaseConfig:
    """从 ``configs/runtime/<name>.yaml`` 加载 YOLO 配置。"""
    from odp_platform.runtime_config.sources import load_yaml_source

    yaml_path = path or runtime_config_path(name)
    kind = task_kind or yaml_path.stem
    if kind not in YOLO_CONFIG_CLASSES:
        raise ValueError(
            f"无法从文件名推断任务类型: {yaml_path.name!r}，"
            f"请显式传入 task_kind（可选: {sorted(YOLO_CONFIG_CLASSES)})"
        )
    raw = load_yaml_source(yaml_path, kind)
    return build_yolo_config(kind, raw)
