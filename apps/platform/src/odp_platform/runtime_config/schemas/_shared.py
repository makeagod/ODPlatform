# -*- coding: utf-8 -*-
"""三类任务共享字段。"""
from odp_platform.common.constants import Task
from odp_platform.runtime_config.fields import FieldSpec

SHARED_META = (
    FieldSpec(
        name="task",
        default=Task.DETECT,
        description="任务语义 (detect/segment)，受平台词汇约束",
        group="meta",
        choices=tuple(Task.all()),
        examples=("detect", "segment"),
        tuning_tips=("命名实验请用 experiment_id，不要用 task 字段",),
    ),
    FieldSpec(
        name="experiment_id",
        default="",
        description="实验标识，仅用于平台目录归档，不传给 Ultralytics",
        group="meta",
        examples=("rsod_baseline_v1", "helmet_aug_test"),
        internal=True,
    ),
    FieldSpec(
        name="data",
        default="",
        description="数据集 YAML 路径（Ultralytics data 参数）",
        group="data",
        examples=("configs/datasets/rsod.yaml",),
    ),
    FieldSpec(
        name="model",
        default="yolo11n.pt",
        description="预训练权重或 checkpoint 路径",
        group="model",
        examples=("yolo11n.pt", "runs/detect/train/weights/best.pt"),
    ),
)
