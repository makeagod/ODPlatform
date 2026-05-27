# -*- coding: utf-8 -*-
from odp_platform.runtime_config.infer import YOLOInferConfig
from odp_platform.runtime_config.infer_build import build_infer_config


def test_build_infer_config_cli_overrides(tmp_path):
    y = tmp_path / "infer.yaml"
    y.write_text(
        "task: detect\nmodel: yolo11n.pt\nsource: image.jpg\nconf: 0.25\n",
        encoding="utf-8",
    )
    config, merger = build_infer_config(
        yaml_path=y,
        cli_args={"conf": 0.5, "source": "0"},
    )
    assert isinstance(config, YOLOInferConfig)
    assert config.conf == 0.5
    assert config.source == "0"
    assert merger.get_metadata("conf") is not None


def test_build_infer_config_cli_only():
    config, _ = build_infer_config(
        yaml_path=__import__("pathlib").Path("/nonexistent/infer.yaml"),
        cli_args={"model": "yolo11n.pt", "source": "demo.jpg"},
    )
    assert config.model == "yolo11n.pt"
    assert config.source == "demo.jpg"
