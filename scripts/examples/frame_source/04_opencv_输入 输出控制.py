#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :04_opencv_输入输出控制.py
import cv2, time
from ultralytics import YOLO

# ── 输入控制:请求摄像头按这个参数采集 ──
CAMERA_WIDTH  = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS    = 90
# ── 输出控制:显示窗口缩放,不影响推理 ──
DISPLAY_WIDTH  = 1280
DISPLAY_HEIGHT = 720

model = YOLO("train3-20250704-165500-yolo11n-best.pt")
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
cap.set(cv2.CAP_PROP_FPS,          CAMERA_FPS)

actual_width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
actual_fps    = cap.get(cv2.CAP_PROP_FPS)
# ★ 修复:摄像头没有总帧数(CAP_PROP_FRAME_COUNT 返回 -1 或 0),单独处理
total_frames  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
if total_frames > 0:
    print(f"摄像头参数: {actual_width}x{actual_height} @ {actual_fps}fps, 总帧数={total_frames}")
else:
    print(f"摄像头参数: {actual_width}x{actual_height} @ {actual_fps}fps (无总帧数)")

frame_index = 0
fps = 0.0
last_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    t_start = time.time()
    results = model(frame, verbose=False)
    t_end = time.time()
    infer_ms = (t_end - t_start) * 1000

    now = time.time()                  # ★ 修复:时间基统一
    fps = 1.0 / (now - last_time)
    last_time = now

    annotated_frame = results[0].plot()
    cv2.putText(annotated_frame, f"FPS: {fps:.2f}",   (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Infer: {infer_ms:.2f} ms", (10,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Frame: {frame_index}", (10,90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Size: {actual_width}x{actual_height}", (10,120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    # 输出控制:缩放显示,推理仍在原始分辨率上做
    if DISPLAY_WIDTH is not None and DISPLAY_HEIGHT is not None:
        display_frame = cv2.resize(annotated_frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT), interpolation=cv2.INTER_LINEAR)
    else:
        display_frame = annotated_frame
    cv2.imshow("YOLOv8 Inference", display_frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    frame_index += 1

cap.release()
cv2.destroyAllWindows()