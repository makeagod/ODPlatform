# -*- coding: utf-8 -*-
from odp_platform.common.provenance_adapter import ProvenanceMergerAdapter
from odp_platform.runtime_config.val import YOLOValConfig
from odp_platform.runtime_config.val_build import build_val_config


def test_build_val_config_returns_pydantic_and_merger(tmp_path):
    y = tmp_path / "val.yaml"
    y.write_text("task: detect\nmodel: yolo11n.pt\nsplit: val\n", encoding="utf-8")
    config, merger = build_val_config(yaml_path=y, cli_args={"batch": 8})
    assert isinstance(config, YOLOValConfig)
    assert isinstance(merger, ProvenanceMergerAdapter)
    assert config.batch == 8
    assert config.split == "val"
    meta = merger.get_metadata("batch")
    assert meta is not None
    assert meta.source_label in ("YAML", "CLI", "DEFAULT")


def test_build_val_config_respects_yaml_split(tmp_path):
    y = tmp_path / "val.yaml"
    y.write_text("task: detect\nmodel: best.pt\nsplit: test\n", encoding="utf-8")
    config, _ = build_val_config(yaml_path=y)
    assert config.split == "test"


def test_build_val_config_cli_overrides_yaml(tmp_path):
    y = tmp_path / "val.yaml"
    y.write_text("task: detect\nmodel: yolo11n.pt\nsplit: val\nconf: 0.001\n", encoding="utf-8")
    config, _ = build_val_config(yaml_path=y, cli_args={"conf": 0.25, "split": "test"})
    assert config.conf == 0.25
    assert config.split == "test"
