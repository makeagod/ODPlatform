#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :08_opencv摄像头测试_智谱清言测试_fixed.py
# @Time      :2026/4/14 10:21:06
# @Author    :雨霓同学
# @Project   :ODPServer
# @Function  :修复 Display FPS 抖动 ——
#             原版 display_fps = 1/Δt 是单帧瞬时倒数,毫秒级抖动 → 显示乱跳
#             改为:30 帧窗口均值 + 文本每秒只刷新一次

import cv2
import time
import threading
from collections import deque

# ══════════════════════════════════════════════════════════════
CAMERA_WIDTH  = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS    = 90

# ★ Display FPS 平滑参数
DISPLAY_FPS_WINDOW       = 10    # 用最近 N 帧的时间戳算均值
DISPLAY_TEXT_REFRESH_SEC = 1.0   # 屏幕上文本每秒才换一次,杜绝末位数字抖
# ══════════════════════════════════════════════════════════════

latest_frame = deque(maxlen=1)
frame_lock = threading.Lock()
real_camera_fps = 0.0
total_captured_frames = 0
capture_start_time = 0.0
running = True


def camera_thread_func():
    """子线程:专职高速采集,计算真实帧率,给画面打水印"""
    global real_camera_fps, running, total_captured_frames, capture_start_time

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

    # 预热
    for _ in range(30):
        cap.read()

    capture_start_time = time.time()
    total_captured_frames = 0
    frame_count = 0
    fps_timer = time.time()

    # ★ Camera FPS 的显示文本:1 秒才换一次
    cam_fps_text = "Camera Real FPS: --"

    while running:
        ret, frame = cap.read()
        if not ret:
            continue

        total_captured_frames += 1
        frame_count += 1

        timestamp = time.time()
        cv2.putText(frame, f"Capture Index: {total_captured_frames}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(frame, f"Time: {timestamp:.3f}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        elapsed = time.time() - fps_timer
        if elapsed >= 1.0:
            real_camera_fps = frame_count / elapsed
            cam_fps_text    = f"Camera Real FPS: {real_camera_fps:.1f}"  # ★ 1 秒换一次
            frame_count = 0
            fps_timer = time.time()

        cv2.putText(frame, cam_fps_text, (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        with frame_lock:
            latest_frame.append(frame)

    cap.release()


t_camera = threading.Thread(target=camera_thread_func, daemon=True)
t_camera.start()

time.sleep(0.05)

print("程序已启动,观察画面左上角:")
print("1. 红色 Index 飞速跳动(证明非重复帧)")
print("2. 绿色 Real FPS 稳定在 90 左右,每秒刷新一次")
print("3. 黄色 Display FPS 稳定在 30 左右,每秒刷新一次")
print("按 Q 或 ESC 退出...")

# ★ 新的平滑机制:窗口均值 + 文本每秒一刷
display_ts_buf   = deque(maxlen=DISPLAY_FPS_WINDOW)
display_fps      = 0.0
display_fps_text = "Display FPS (GUI): --"
last_text_update = 0.0

while running:
    with frame_lock:
        frame_to_show = latest_frame[-1].copy() if latest_frame else None

    if frame_to_show is not None:
        now = time.time()
        display_ts_buf.append(now)

        # ★ 用窗口均值代替单帧瞬时倒数,且每秒才更新一次显示文本
        if now - last_text_update >= DISPLAY_TEXT_REFRESH_SEC and len(display_ts_buf) >= 2:
            display_fps      = (len(display_ts_buf) - 1) / (display_ts_buf[-1] - display_ts_buf[0])
            display_fps_text = f"Display FPS (GUI): {display_fps:.1f}"
            last_text_update = now

        cv2.putText(frame_to_show, display_fps_text, (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        cv2.imshow("Async Camera Test", frame_to_show)

    key = cv2.waitKey(1)
    if key == ord('q') or key == 27:
        break

running = False
t_camera.join()

total_time = time.time() - capture_start_time
avg_fps = total_captured_frames / total_time if total_time > 0 else 0

cv2.destroyAllWindows()

print("=" * 45)
print(" 异步采集最终统计")
print("=" * 45)
print(f" 总采集帧数:     {total_captured_frames} 帧")
print(f" 总实际耗时:     {total_time:.1f} 秒")
print(f" 综合平均帧率:   {avg_fps:.1f} FPS")
print("=" * 45)
print(f" 结论: 摄像头满速跑了 {avg_fps:.1f} FPS,")
print(f"       但 OpenCV 窗口只渲染了 {display_fps:.1f} FPS,")
print(f"       中间差值的帧被 deque 自动丢弃,保证了画面无延迟。")
print("=" * 45)