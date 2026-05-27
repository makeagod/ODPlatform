#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""终态示例：frame_source 统一出帧 + ultralytics 推理（与源类型无关的循环）。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
from ultralytics import YOLO

from odp_platform.common.model_path import resolve_model_path
from odp_platform.frame_source import (
    CameraConfig,
    create_frame_source,
    create_threaded_source,
)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="frame_source + YOLO 推理演示")
    p.add_argument("--source", default="0", help="0=摄像头 / 视频路径 / 图片 / 目录")
    p.add_argument("--model", default="yolov8n.pt", help="权重（models/pretrained 或绝对路径）")
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--backend", default="msmf", help="摄像头后端: msmf / dshow / v4l2")
    p.add_argument("--max-frames", type=int, default=0, help="0=不限制")
    p.add_argument("--no-show", action="store_true", help="不弹窗，只打印帧信息")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    model_path = resolve_model_path(args.model)
    model = YOLO(str(model_path))

    cam_cfg = None
    if args.source.isdigit():
        cam_cfg = CameraConfig(
            width=args.width,
            height=args.height,
            fps=args.fps,
            backend=args.backend,
        )

    kwargs = {}
    if cam_cfg is not None:
        kwargs["camera_config"] = cam_cfg

    n = 0
    if args.source.isdigit():
        ctx = create_threaded_source(args.source, warmup_frames=15, **kwargs)
    else:
        ctx = create_frame_source(args.source, **kwargs)

    with ctx as src:
        for frame in src:
            results = model.predict(frame.image, verbose=False)
            vis = results[0].plot()
            info = frame.info
            print(
                f"[{info.frame_index}] {frame.width}x{frame.height} "
                f"file={info.filename!r}"
            )
            if not args.no_show:
                cv2.imshow("frame_source + YOLO", vis)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
            n += 1
            if args.max_frames and n >= args.max_frames:
                break

    if not args.no_show:
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
