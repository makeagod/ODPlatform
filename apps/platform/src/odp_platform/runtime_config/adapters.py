# -*- coding: utf-8 -*-
"""动态多后端适配器 (Multi-Backend Adapter)。

通过适配器模式将 RuntimeConfig 翻译为不同训练框架的原生参数字典。
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

from odp_platform.runtime_config.config_object import RuntimeConfig


def _set_nested(d: dict[str, Any], path: str, value: Any) -> None:
    """按点号分隔路径写入嵌套字典，自动创建中间层级。"""
    keys = path.split(".")
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


class BaseBackendAdapter(ABC):
    """后端适配器抽象基类。

    每个子类负责将统一的 RuntimeConfig 翻译为特定框架的参数字典。
    """

    @abstractmethod
    def translate(self, runtime_config: RuntimeConfig) -> dict[str, Any]:
        """将 RuntimeConfig 翻译为目标框架的参数字典。"""
        ...

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """返回后端标识名，如 "ultralytics"、"mmdetection"。"""
        ...


class UltralyticsAdapter(BaseBackendAdapter):
    """Ultralytics YOLO 框架适配器。

    过滤平台内部字段和空值，产出可直接传入 model.train() 的 kwargs。
    """

    @property
    def backend_name(self) -> str:
        return "ultralytics"

    def translate(self, runtime_config: RuntimeConfig) -> dict[str, Any]:
        out: dict[str, Any] = {}
        internal = runtime_config.schema.internal_fields
        for key, val in runtime_config.values.items():
            if key in internal:
                continue
            if val is None:
                continue
            if val == "" and key not in ("device",):
                continue
            # 字段映射：如平台内部用 lr 则映射为 Ultralytics 的 lr0
            out[key] = val
        return out


class MMDetectionAdapter(BaseBackendAdapter):
    """MMDetection 框架适配器。

    将扁平的 RuntimeConfig 翻译为 MMDetection 所需的深层嵌套 Config dict。
    仅映射有对应关系的字段，其余忽略。
    """

    # 平台字段 → MMDetection 嵌套路径
    _FIELD_MAP: dict[str, str] = {
        "batch": "train_dataloader.batch_size",
        "workers": "train_dataloader.num_workers",
        "lr0": "optim_wrapper.optimizer.lr",
        "epochs": "train_cfg.max_epochs",
        "seed": "randomness.seed",
        "imgsz": "train_pipeline.img_scale",
    }

    @property
    def backend_name(self) -> str:
        return "mmdetection"

    def translate(self, runtime_config: RuntimeConfig) -> dict[str, Any]:
        result: dict[str, Any] = {}
        vals = runtime_config.values
        has_lr = "lr0" in vals and vals["lr0"] is not None

        # 基础结构默认值
        result["train_dataloader"] = {}
        result["val_dataloader"] = {}
        result["optim_wrapper"] = {"optimizer": {}}
        result["train_cfg"] = {"type": "EpochBasedTrainLoop"}
        result["randomness"] = {}
        result.setdefault("default_hooks", {}).setdefault("checkpoint", {})

        # 字段映射
        for plat_key, mm_path in self._FIELD_MAP.items():
            if plat_key in vals and vals[plat_key] is not None:
                _set_nested(result, mm_path, vals[plat_key])

        # batch / workers 同步到 val_dataloader
        if "batch" in vals and vals["batch"] is not None:
            _set_nested(result, "val_dataloader.batch_size", vals["batch"])
        if "workers" in vals and vals["workers"] is not None:
            _set_nested(result, "val_dataloader.num_workers", vals["workers"])

        # imgsz — MMDetection 用 (w, h) 元组
        if "imgsz" in vals and vals["imgsz"] is not None:
            sz = vals["imgsz"]
            _set_nested(result, "train_pipeline.img_scale", (sz, sz))
            result.setdefault("test_pipeline", {})["img_scale"] = (sz, sz)
            result.setdefault("val_pipeline", {})["img_scale"] = (sz, sz)

        # 早停
        if vals.get("patience", -1) > 0:
            _set_nested(result, "param_scheduler.early_stop_patience", vals["patience"])

        # work_dir
        project = vals.get("project", "") or ""
        name = vals.get("name", "") or ""
        if project or name:
            result["work_dir"] = os.path.join(project, name).replace("\\", "/") if name else project.replace("\\", "/")

        # 默认优化器参数：仅当 lr 被显式设置时才补充
        if has_lr:
            opt = result["optim_wrapper"]["optimizer"]
            opt.setdefault("type", "SGD")
            opt.setdefault("momentum", 0.9)
            opt.setdefault("weight_decay", 0.0001)

        return result


# ── 适配器注册表 ────────────────────────────────────────────────────────────

_ADAPTERS: dict[str, BaseBackendAdapter] = {
    "ultralytics": UltralyticsAdapter(),
    "mmdetection": MMDetectionAdapter(),
}


def get_adapter(backend_type: str) -> BaseBackendAdapter:
    """根据后端类型名获取适配器实例。"""
    if backend_type not in _ADAPTERS:
        raise ValueError(
            f"未知后端类型: {backend_type!r}，可选: {list(_ADAPTERS.keys())}"
        )
    return _ADAPTERS[backend_type]


def register_adapter(backend_type: str, adapter: BaseBackendAdapter) -> None:
    """注册自定义后端适配器（插件式扩展）。"""
    _ADAPTERS[backend_type] = adapter
