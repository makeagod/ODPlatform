#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : ex03_输入输出控制.py
# @Project   : ODPlatform / frame_source examples
# @Function  : 替代原始脚本【04_opencv_输入输出控制.py + 05_..._真实输入输出测试.py】
#              输入控制 = 填一个 CameraConfig;输出控制 = 自己 resize
"""
对照原始脚本 04 / 05:
  - 04 手写 cap.set(WIDTH/HEIGHT/FPS) 再 cap.get 读回,参数散在代码里
  - 05 还要自己写"实测帧率":每秒数帧、对比标称值,防止被 cap.get 的标称值骗

frame_source 之后:
  - "set 是请求 / get 要验证 / fps 要实测 / 后端要选对"这一整套(撞墙③④⑤)
    全部封进 CameraSource.open() 内部;调用方只填一个 CameraConfig 声明意图
  - 输出控制(显示缩放)仍是调用方的事 —— 推理在原始分辨率上做,resize 只动显示
"""
import cv2
from ultralytics import YOLO

from odp_platform.frame_source import CameraConfig, create_frame_source

# ── 输入控制:声明你要的采集参数(高帧率在 Windows 下自动走 MSMF + MJPG)──
CAM = CameraConfig(width=1280, height=720, fps=90, backend="msmf", codec="MJPG")

# ── 输出控制:显示窗口缩放到多大(None 表示不缩放)──
DISPLAY = (1280, 720)

model = YOLO("train3-20250704-165500-yolo11n-best.pt")

with create_frame_source("0", camera_config=CAM) as src:
    for frame in src:
        results = model(frame.image, verbose=False)
        annotated = results[0].plot()

        # 实际生效的采集尺寸/标称帧率,直接读 frame.info(已经是协商后的真值)
        info = frame.info
        cv2.putText(annotated, f"Capture : {info.width}x{info.height} @ {info.fps}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # 输出控制:只缩放显示,不影响推理输入
        display = cv2.resize(annotated, DISPLAY, interpolation=cv2.INTER_LINEAR) if DISPLAY else annotated
        cv2.imshow("frame_source · ex03", display)
        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            break

cv2.destroyAllWindows()
