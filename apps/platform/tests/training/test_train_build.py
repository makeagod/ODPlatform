# -*- coding: utf-8 -*-
from odp_platform.common.model_path import resolve_model_path
from odp_platform.common.provenance_adapter import ProvenanceMergerAdapter
from odp_platform.runtime_config.train import YOLOTrainConfig
from odp_platform.runtime_config.train_build import build_train_config


def test_build_train_config_returns_pydantic_and_merger(tmp_path):
    y = tmp_path / "train.yaml"
    y.write_text("epochs: 7\ntask: detect\nmodel: yolo11n.pt\n", encoding="utf-8")
    config, merger = build_train_config(yaml_path=y, cli_args={"batch": 4})
    assert isinstance(config, YOLOTrainConfig)
    assert isinstance(merger, ProvenanceMergerAdapter)
    assert config.epochs == 7
    assert config.batch == 4
    meta = merger.get_metadata("epochs")
    assert meta is not None
    assert meta.source_label in ("YAML", "CLI", "DEFAULT")


def test_resolve_model_path_relative_name():
    p = resolve_model_path("yolo11n.pt")
    assert p.name == "yolo11n.pt"
