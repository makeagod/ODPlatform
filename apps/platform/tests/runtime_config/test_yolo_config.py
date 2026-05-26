# -*- coding: utf-8 -*-
from pathlib import Path

import pytest
from pydantic import ValidationError

from odp_platform.common.paths import RUNTIME_CONFIGS_DIR, runtime_config_path
from odp_platform.runtime_config import (
    YOLOTrainConfig,
    build_train_config,
    build_yolo_config,
    normalize_for_pydantic,
)
from odp_platform.runtime_config.loader import load_yolo_config_from_yaml


def test_runtime_config_path_d5():
    p = runtime_config_path("train")
    assert p == RUNTIME_CONFIGS_DIR / "train.yaml"
    assert runtime_config_path("val.yaml") == RUNTIME_CONFIGS_DIR / "val.yaml"


def test_experiment_id_alias():
    cfg = build_yolo_config(
        "train",
        normalize_for_pydantic(
            {"task": "detect", "experiment_id": "rsod_v1", "epochs": 10}
        ),
    )
    assert isinstance(cfg, YOLOTrainConfig)
    assert cfg.experiment_name == "rsod_v1"
    assert cfg.epochs == 10


def test_to_ultralytics_strips_framework_fields():
    cfg = build_yolo_config(
        "train",
        {
            "task": "detect",
            "experiment_name": "exp1",
            "verbose": True,
            "epochs": 5,
            "model": "yolo11n.pt",
        },
    )
    kw = cfg.to_ultralytics_kwargs()
    assert "experiment_name" not in kw
    assert "verbose" not in kw
    assert kw["epochs"] == 5


def test_build_train_config_to_backend(tmp_path):
    y = tmp_path / "train.yaml"
    y.write_text(
        "task: detect\nexperiment_id: t1\nepochs: 12\nmodel: yolo11n.pt\n",
        encoding="utf-8",
    )
    rc = build_train_config(yaml_path=y)
    kw = rc.to_backend_kwargs("ultralytics")
    assert kw["epochs"] == 12
    assert "experiment_id" not in kw


def test_save_save_period_cross_field():
    with pytest.raises(ValidationError):
        build_yolo_config(
            "train",
            {"task": "detect", "save": False, "save_period": 5},
        )


def test_load_yolo_config_from_yaml_repo():
    path = runtime_config_path("train")
    if not path.exists():
        pytest.skip("configs/runtime/train.yaml 不存在")
    cfg = load_yolo_config_from_yaml("train")
    assert cfg.task == "detect"
