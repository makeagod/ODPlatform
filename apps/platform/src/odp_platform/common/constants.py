# -*- coding: utf-8 -*-
"""D3 共享词汇表常量定义"""


class AnnotationFormat:
    PASCAL_VOC = "pascal_voc"
    COCO = "coco"
    YOLO = "yolo"


class Task:
    DETECT = "detect"
    SEGMENT = "segment"


# 兼容旧代码字符串别名
PASCAL_VOC = AnnotationFormat.PASCAL_VOC
COCO = AnnotationFormat.COCO
YOLO = AnnotationFormat.YOLO
TASK_DETECT = Task.DETECT
TASK_SEGMENT = Task.SEGMENT

# D4 data_validation — 图像扩展名（含大小写变体，跨平台）
IMAGE_EXTENSIONS: tuple[str, ...] = (
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".JPG",
    ".JPEG",
    ".PNG",
    ".BMP",
    ".WEBP",
)

# pair_existence 缺失比例阈值
PAIR_MISSING_ERROR_RATIO: float = 0.5
PAIR_MISSING_WARN_RATIO: float = 0.05

# JSON / details 预览条数上限
DETAILS_PREVIEW_LIMIT: int = 20
