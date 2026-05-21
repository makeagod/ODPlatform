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
