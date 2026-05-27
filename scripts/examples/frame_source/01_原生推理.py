#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :01_原生推理.py
# @Time      :2026/5/27 09:18:37
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :
from torch._C import device
from ultralytics import YOLO

model = YOLO("./train3-20250704-165500-yolo11n-best.pt")
model.predict(source="0", show=True, device='0')

