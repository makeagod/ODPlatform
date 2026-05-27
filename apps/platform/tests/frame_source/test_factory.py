# -*- coding: utf-8 -*-
"""frame_source 工厂与图片源（无需摄像头）。"""
from __future__ import annotations

import cv2
import numpy as np

from odp_platform.frame_source import (
    CameraConfig,
    create_frame_source,
    create_threaded_source,
)


def test_single_image_source(tmp_path):
    img = tmp_path / "probe.jpg"
    cv2.imwrite(str(img), np.zeros((16, 16, 3), dtype=np.uint8))

    with create_frame_source(str(img)) as src:
        frames = list(src)

    assert len(frames) == 1
    assert frames[0].width == 16
    assert frames[0].height == 16
    assert frames[0].info.frame_index == 0


def test_image_folder_source(tmp_path):
    for i in range(3):
        p = tmp_path / f"{i}.jpg"
        cv2.imwrite(str(p), np.full((8, 8, 3), i * 40, dtype=np.uint8))

    with create_frame_source(str(tmp_path)) as src:
        frames = list(src)

    assert len(frames) == 3


def test_camera_config_factory():
    cfg = CameraConfig(width=640, height=480, fps=30, backend="msmf")
    src = create_frame_source("0", camera_config=cfg)
    assert src is not None
    # 不 open，避免 CI 无摄像头失败


def test_threaded_factory_returns_wrapper():
    src = create_threaded_source("0", warmup_frames=0)
    assert type(src).__name__ == "ThreadedSource"
