#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :03_opencv_叠加信息显示.py
# @Time      :2026/5/27 09:33:53
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :03_opencv_叠加信息显示.py
import cv2, time
from ultralytics import YOLO

model = YOLO("train3-20250704-165500-yolo11n-best.pt")
cap = cv2.VideoCapture(0)

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
    infer_ms = (t_end - t_start) * 1000          # 单帧推理耗时

    # ★ 修复:原版 dt 用 time.time() 但 last_time 存的是 t_end,时间基混用
    now = time.time()
    fps = 1.0 / (now - last_time)                 # 循环帧率
    last_time = now
    h, w = frame.shape[:2]                         # 当前帧尺寸

    annotated_frame = results[0].plot()
    cv2.putText(annotated_frame, f"FPS: {fps:.2f}",          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Infer: {infer_ms:.2f} ms", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Frame: {frame_index}",     (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(annotated_frame, f"Resolution: {w}x{h}",      (10,120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("YOLOv8 Inference", annotated_frame)
    # ★ 修复:pollKey 不驱动窗口事件循环,Windows/macOS 上窗口可能不刷新或假死
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break
    frame_index += 1

cap.release()
cv2.destroyAllWindows()