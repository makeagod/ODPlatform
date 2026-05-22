# -*- coding: utf-8 -*-
from typing import Any, Optional

from odp_platform.runtime_config.fields import FieldSpec, TaskSchema
from odp_platform.runtime_config.schemas._shared import SHARED_META


def _train_cross_field(values: dict[str, Any]) -> Optional[str]:
    if values.get("save") is False and values.get("save_period", -1) not in (-1, 0):
        return "save=false 与 save_period>0 矛盾，请澄清是否保存 checkpoint"
    return None


def _train_cross_warn(values: dict[str, Any]) -> Optional[str]:
    if values.get("mosaic", 1.0) == 0.0 and values.get("close_mosaic", 0) > 0:
        return "mosaic=0 时 close_mosaic 不会生效（冗余配置）"
    return None


TRAIN_FIELDS = SHARED_META + (
    FieldSpec("epochs", 100, "训练轮数", "train", ("50", "100", "300"), min_value=1),
    FieldSpec("imgsz", 640, "输入图像尺寸", "train", ("640", "1280"), min_value=32),
    FieldSpec("batch", 16, "批次大小；-1 为自动", "train", ("16", "32", "-1"), min_value=-1),
    FieldSpec("device", "", "训练设备，如 0 或 cpu", "train", ("0", "cpu", "0,1")),
    FieldSpec("workers", 8, "DataLoader 工作进程数", "train", min_value=0),
    FieldSpec("lr0", 0.01, "初始学习率", "train", min_value=0.0),
    FieldSpec("project", "runs/detect", "Ultralytics project 目录", "train"),
    FieldSpec("name", "train", "本次运行名称", "train"),
    FieldSpec("save", True, "是否保存 checkpoint", "train"),
    FieldSpec("save_period", -1, "按 epoch 保存周期；-1 禁用周期保存", "train", min_value=-1),
    FieldSpec("patience", 100, "早停 patience", "train", min_value=0),
    FieldSpec("seed", 0, "随机种子", "train"),
    FieldSpec("verbose", True, "详细日志", "train"),
    FieldSpec("mosaic", 1.0, "Mosaic 增强概率", "augment", min_value=0.0, max_value=1.0),
    FieldSpec("close_mosaic", 10, "最后 N epoch 关闭 mosaic", "augment", min_value=0),
)

TRAIN_SCHEMA = TaskSchema(
    task_kind="train",
    fields=TRAIN_FIELDS,
    internal_fields=frozenset({"experiment_id"}),
    cross_field_validators=(_train_cross_field,),
)

TRAIN_WARN_VALIDATORS = (_train_cross_warn,)
