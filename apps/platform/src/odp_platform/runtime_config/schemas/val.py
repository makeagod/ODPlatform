# -*- coding: utf-8 -*-
from odp_platform.runtime_config.fields import FieldSpec, TaskSchema
from odp_platform.runtime_config.schemas._shared import SHARED_META

VAL_FIELDS = SHARED_META + (
    # 核心参数在 SHARED_META: task, experiment_id, data, model

    # 验证控制
    FieldSpec("split", "val", "数据集划分", "val", examples=("val", "test", "train"), choices=("val", "test", "train")),
    FieldSpec("conf", 0.001, "置信度阈值", "val", examples=("0.001", "0.25"), min_value=0.0, max_value=1.0),
    FieldSpec("iou", 0.6, "NMS IoU 阈值", "val", min_value=0.0, max_value=1.0),
    FieldSpec("max_det", 300, "每张图最大检测数", "val", min_value=1),

    # 输入配置
    FieldSpec("imgsz", 640, "输入图像尺寸", "val", min_value=32),
    FieldSpec("batch", 16, "批次大小", "val", min_value=-1),
    FieldSpec("workers", 8, "DataLoader 工作进程数", "val", min_value=0),

    # 设备配置
    FieldSpec("device", "", "设备（0/cpu/0,1）", "val", examples=("0", "cpu")),
    FieldSpec("amp", True, "自动混合精度", "val"),

    # 评估设置
    FieldSpec("half", True, "半精度推理", "val"),
    FieldSpec("plots", True, "生成评估图表", "val"),
    FieldSpec("save_json", True, "保存 COCO JSON", "val"),
    FieldSpec("save_hybrid", False, "保存混合标签", "val"),

    # 输出配置
    FieldSpec("project", "runs/detect", "project 目录", "val"),
    FieldSpec("name", "val", "运行名称", "val"),
    FieldSpec("exist_ok", False, "覆盖已有目录", "val"),
    FieldSpec("verbose", True, "详细日志", "val"),
    FieldSpec("save", True, "保存检查点", "val"),

    # 基础设置
    FieldSpec("seed", 0, "随机种子", "val", min_value=0),
    FieldSpec("deterministic", True, "确定性算法", "val"),

    # 数据加载
    FieldSpec("cache", False, "数据缓存(False/True/ram/disk)", "val"),
    FieldSpec("rect", False, "矩形推理", "val"),

    # 任务特定
    FieldSpec("mask_ratio", 4, "掩码下采样比例(分割)", "val", min_value=1),
    FieldSpec("overlap_mask", True, "重叠掩码(分割)", "val"),
    FieldSpec("dnn", False, "OpenCV DNN 后端", "val"),
)

VAL_SCHEMA = TaskSchema(
    task_kind="val",
    fields=VAL_FIELDS,
    internal_fields=frozenset({"experiment_id", "task"}),
)
