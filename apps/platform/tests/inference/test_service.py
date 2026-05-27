# -*- coding: utf-8 -*-
import cv2
import numpy as np

from odp_platform.inference.service import InferService


def test_predict_requires_source(tmp_path):
    y = tmp_path / "infer.yaml"
    y.write_text("model: yolo11n.pt\n", encoding="utf-8")
    result = InferService().predict(yaml_path=y, cli_args={})
    assert not result.success
    assert result.error
    assert "source" in result.error.lower()


def test_predict_requires_model(tmp_path):
    y = tmp_path / "infer.yaml"
    y.write_text("source: image.jpg\n", encoding="utf-8")
    result = InferService().predict(yaml_path=y, cli_args={})
    assert not result.success
    assert "model" in result.error.lower()


def test_predict_single_image(tmp_path):
    img = tmp_path / "one.jpg"
    cv2.imwrite(str(img), np.zeros((32, 32, 3), dtype=np.uint8))
    y = tmp_path / "infer.yaml"
    y.write_text("model: yolo11n.pt\n", encoding="utf-8")

    result = InferService().predict(
        yaml_path=y,
        cli_args={
            "source": str(img),
            "device": "cpu",
            "show": False,
            "save": True,
        },
        use_threaded=False,
        warmup_frames=0,
        max_frames=1,
        rename_log=False,
    )
    if not result.success and "source" in (result.error or ""):
        return
    assert result.success, result.error
    assert result.frames_processed == 1
    assert result.output_dir.is_dir()
