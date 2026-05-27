#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :07_opencv摄像头测试_fixed.py
# @Time      :2026/4/14 10:17:12
# @Author    :雨霓同学
# @Project   :ODPServer
# @Function  :修复 GUI FPS 文本抖动 —— 计算照旧 (30 帧窗口),
#             但显示字符串每 1 秒才刷新一次,眼睛不再被末位数字晃

import cv2
import time
import threading
import queue

# ══════════════════════════════════════════════════════════════
CAMERA_INDEX  = 0
CAMERA_WIDTH  = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS    = 90
CAMERA_FOURCC = "MJPG"

# ★ 新增:GUI FPS 显示文本刷新间隔(秒)。底层采样仍按窗口算,
#    只是贴到画面上的字符串隔多久才换一次。1.0 秒对齐 06 的观感。
DISPLAY_TEXT_REFRESH_SEC = 1.0
# ══════════════════════════════════════════════════════════════


def fourcc_to_str(fourcc_int: int) -> str:
    return "".join([chr((int(fourcc_int) >> (8 * i)) & 0xFF) for i in range(4)])


frame_queue: queue.Queue = queue.Queue(maxsize=1)
running = threading.Event()
running.set()

stats = {
    "total_frames": 0,
    "capture_start": None,
    "capture_end":   None,
}
stats_lock = threading.Lock()


def camera_thread_func():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_ANY)
    cap.set(cv2.CAP_PROP_FOURCC,      cv2.VideoWriter_fourcc(*CAMERA_FOURCC))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,         CAMERA_FPS)

    actual_w      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps    = cap.get(cv2.CAP_PROP_FPS)
    actual_fourcc = fourcc_to_str(cap.get(cv2.CAP_PROP_FOURCC))
    backend_name  = cap.getBackendName()

    print("═" * 50)
    print(f"  后端 (Backend)  : {backend_name}")
    print(f"  编码 (FOURCC)   : {actual_fourcc}")
    print(f"  分辨率          : {actual_w} × {actual_h}")
    print(f"  驱动申报 FPS    : {actual_fps}")
    print("═" * 50)

    for _ in range(30):
        cap.read()

    with stats_lock:
        stats["capture_start"] = time.perf_counter()

    frame_count  = 0
    total_frames = 0
    real_fps     = 0.0
    fps_timer    = time.perf_counter()

    # ★ Cam FPS 的显示字符串:1 秒才换一次,期间画面上文字稳定
    cam_fps_text = "Cam FPS: --"

    info_text = [
        f"Backend : {backend_name}",
        f"FOURCC  : {actual_fourcc}",
        f"Set: {CAMERA_WIDTH}x{CAMERA_HEIGHT}@{CAMERA_FPS}  "
        f"Got: {actual_w}x{actual_h}@{actual_fps:.0f}",
    ]

    while running.is_set():
        ret, frame = cap.read()
        if not ret:
            continue

        total_frames += 1
        frame_count  += 1

        now     = time.perf_counter()
        elapsed = now - fps_timer
        if elapsed >= 1.0:
            real_fps     = frame_count / elapsed
            cam_fps_text = f"Cam FPS: {real_fps:.1f}"   # ★ 1 秒才更新一次文本
            frame_count  = 0
            fps_timer   += elapsed

        display = frame.copy()
        ts = time.perf_counter()
        cv2.putText(display, f"Index : {total_frames}",   (10, 35),  cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0,   0,   255), 2)
        cv2.putText(display, f"Time  : {ts:.4f}",         (10, 70),  cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0,   0,   255), 2)
        cv2.putText(display, cam_fps_text,                (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0,   255,   0), 2)
        for i, line in enumerate(info_text):
            cv2.putText(display, line, (10, actual_h - 20 - i * 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 1)

        try:
            frame_queue.get_nowait()
        except queue.Empty:
            pass
        frame_queue.put(display)

        with stats_lock:
            stats["total_frames"] = total_frames

    with stats_lock:
        stats["capture_end"] = time.perf_counter()

    cap.release()


t_camera = threading.Thread(target=camera_thread_func, daemon=True)
t_camera.start()
print("按 Q 或 ESC 退出...\n")

DISPLAY_FPS_WINDOW = 30
ts_buf = []
display_fps      = 0.0
display_fps_text = "GUI FPS: --"   # ★ 屏幕上显示的字符串
last_text_update = 0.0             # ★ 上次刷新显示文本的时间

while True:
    try:
        frame_to_show = frame_queue.get(timeout=0.05)
    except queue.Empty:
        if cv2.waitKey(1) in (ord('q'), 27):
            break
        continue

    now = time.perf_counter()
    ts_buf.append(now)
    if len(ts_buf) > DISPLAY_FPS_WINDOW:
        ts_buf.pop(0)

    # ★ 关键:计算照旧,但每秒才把数值"落"成新的显示字符串
    if now - last_text_update >= DISPLAY_TEXT_REFRESH_SEC and len(ts_buf) >= 2:
        display_fps      = (len(ts_buf) - 1) / (ts_buf[-1] - ts_buf[0])
        display_fps_text = f"GUI FPS: {display_fps:.1f}"
        last_text_update = now

    cv2.putText(frame_to_show, display_fps_text, (10, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 0), 2)
    cv2.imshow("Async Camera Test", frame_to_show)

    if cv2.waitKey(1) in (ord('q'), 27):
        break

running.clear()
t_camera.join()
cv2.destroyAllWindows()

with stats_lock:
    total   = stats["total_frames"]
    t_start = stats["capture_start"]
    t_end   = stats["capture_end"]

duration = (t_end - t_start) if (t_start and t_end) else 0.0
avg_fps  = total / duration if duration > 0 else 0.0

print()
print("═" * 50)
print(f"  总采集帧数  : {total} 帧")
print(f"  有效采集时长: {duration:.3f} 秒  (预热30帧已排除)")
print(f"  平均真实FPS : {avg_fps:.2f} fps")
print("═" * 50)