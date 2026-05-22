# -*- coding: utf-8 -*-
from odp_platform.runtime_config.fields import FieldSpec, TaskSchema
from odp_platform.runtime_config.schemas._shared import SHARED_META

VAL_FIELDS = SHARED_META + (
    FieldSpec("imgsz", 640, "验证图像尺寸", "val", min_value=32),
    FieldSpec("batch", 16, "验证批次", "val", min_value=-1),
    FieldSpec("device", "", "设备", "val"),
    FieldSpec("split", "val", "数据划分", "val", choices=("val", "test", "train")),
    FieldSpec("project", "runs/detect", "project 目录", "val"),
    FieldSpec("name", "val", "运行名称", "val"),
    FieldSpec("verbose", True, "详细日志", "val"),
)

VAL_SCHEMA = TaskSchema(
    task_kind="val",
    fields=VAL_FIELDS,
    internal_fields=frozenset({"experiment_id", "task"}),
)
