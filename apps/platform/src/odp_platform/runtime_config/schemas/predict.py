# -*- coding: utf-8 -*-
from odp_platform.runtime_config.fields import FieldSpec, TaskSchema
from odp_platform.runtime_config.schemas._shared import SHARED_META

PREDICT_FIELDS = SHARED_META + (
    FieldSpec("imgsz", 640, "推理图像尺寸", "predict", min_value=32),
    FieldSpec("conf", 0.25, "置信度阈值", "predict", min_value=0.0, max_value=1.0),
    FieldSpec("iou", 0.7, "NMS IoU 阈值", "predict", min_value=0.0, max_value=1.0),
    FieldSpec("device", "", "设备", "predict"),
    FieldSpec("project", "runs/detect", "project 目录", "predict"),
    FieldSpec("name", "predict", "运行名称", "predict"),
    FieldSpec("save", True, "是否保存预测结果", "predict"),
    FieldSpec("verbose", True, "详细日志", "predict"),
)

PREDICT_SCHEMA = TaskSchema(
    task_kind="predict",
    fields=PREDICT_FIELDS,
    internal_fields=frozenset({"experiment_id", "task"}),
)
