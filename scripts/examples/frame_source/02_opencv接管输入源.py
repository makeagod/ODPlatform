#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :02-opencv接管输入源.py
import cv2
from ultralytics import YOLO

model = YOLO("train3-20250704-165500-yolo11n-best.pt")
cap = cv2.VideoCapture(0)          # ← 自己开摄像头

while True:
    ret, frame = cap.read()        # ← 控制点①:现在能在这里插逻辑了
    if not ret:
        break


    results = model(frame, verbose=False)   # ← 控制点②:推单帧,results 自己处理
    annotated_frame = results[0].plot()      # ← 控制点③:也可以不用 plot,自己画

    cv2.imshow("YOLOv8 Inference", annotated_frame)
    # ★ 修复:原版 waitKey(1) 被调用两次,第一次即消费按键,第二次永远拿不到 ESC
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break

cap.release()
cv2.destroyAllWindows()