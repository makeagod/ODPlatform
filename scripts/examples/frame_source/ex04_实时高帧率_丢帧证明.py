#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : ex04_实时高帧率_丢帧证明.py
# @Project   : ODPlatform / frame_source examples
# @Function  : 替代原始脚本【06_摄像头后端自己选择 + 07_..._测试 + 08_..._多线程】
#              三个脚本的全部价值,塌缩成一个 create_threaded_source(...)
"""
对照原始脚本 06 / 07 / 08(三个加起来 ~400 行):
  - 06: 显式 MSMF 后端 + MJPG + 禁用硬件变换 + 采集/显示双线程 + 锁保护最新帧
  - 07: queue(maxsize=1) 传帧 + 显示文本节流
  - 08: deque(maxlen=1) 自动丢帧 + 用帧号实证"采集满速、显示丢帧"

frame_source 之后:
  - 后端协商(撞墙⑤)→ 封进 CameraSource
  - 采集/显示双线程(撞墙⑥)→ 封进 ThreadedSource
  - 宁丢勿堆 buffer="latest"(撞墙⑦)→ ThreadedSource 默认行为
  - 整个高帧率基准 = 一行 create_threaded_source(..., warmup_frames=30)
  - 撞墙⑧的"丢帧证明"现在白拿:消费到的相邻 frame.info.frame_index 跳变 = 被丢的帧
"""
import time

import cv2
from ultralytics import YOLO

from frame_source import CameraConfig, create_threaded_source

CAM = CameraConfig(width=1280, height=720, fps=90, backend="msmf", codec="MJPG")

model = YOLO("train3-20250704-165500-yolo11n-best.pt")

last = time.time()
display_fps = 0.0
prev_capture_index = None     # 上一帧的采集序号,用来看跳变
total_dropped = 0             # 累计被丢弃的采集帧数(= 采集满速的证据)

# warmup_frames=30:丢掉 MSMF 前 30 帧不稳的预热阶段(原 06/07/08 都手写了这个)
with create_threaded_source("0", camera_config=CAM, warmup_frames=30) as src:
    for frame in src:
        results = model(frame.image, verbose=False)
        annotated = results[0].plot()

        now = time.time()
        display_fps = 1.0 / (now - last)
        last = now

        # ── 丢帧证明(原脚本 08 的核心,现在免费)──
        cap_idx = frame.info.frame_index            # 采集端序号(穿过线程不变)
        if prev_capture_index is not None:
            gap = cap_idx - prev_capture_index      # 两次消费之间,采集端前进了多少
            if gap > 1:
                total_dropped += gap - 1            # 中间 gap-1 帧被 latest 缓冲丢了
        prev_capture_index = cap_idx

        cv2.putText(annotated, f"Display FPS : {display_fps:5.1f}",       (10, 30),  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(annotated, f"Capture Idx : {cap_idx}  (jumps=satur)", (10, 60),  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
        cv2.putText(annotated, f"Dropped     : {total_dropped}",          (10, 90),  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (180, 180, 180), 2)
        cv2.putText(annotated, f"Cam nominal : {frame.info.fps} fps",     (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (180, 180, 180), 2)

        cv2.imshow("frame_source · ex04 (threaded)", annotated)
        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            break

cv2.destroyAllWindows()

print("=" * 48)
print("  采集端序号一直在跳(Capture Idx),说明摄像头满速跑;")
print(f"  消费端只看到其中一部分,被丢弃 {total_dropped} 帧 —— ")
print("  这正是 ThreadedSource buffer='latest' 的宁丢勿堆,保证画面无延迟。")
print("=" * 48)
