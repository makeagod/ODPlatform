# -*- coding: utf-8 -*-
from argparse import Namespace

import pytest

from odp_platform.runtime_config.exceptions import ConfigFileNotFoundError
from odp_platform.runtime_config.loaders import (
    CLILoader,
    YAMLLoader,
    drop_none_values,
    load_all_sources,
)
from odp_platform.runtime_config.sources import load_yaml_source


def test_drop_none_keeps_falsy():
    assert drop_none_values({"a": None, "b": False, "c": 0, "d": ""}) == {
        "b": False,
        "c": 0,
        "d": "",
    }


def test_yaml_loader_empty_file(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    assert YAMLLoader().load(p) == {}


def test_yaml_loader_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError) as exc:
        YAMLLoader().load(tmp_path / "nope.yaml")
    assert "odp-gen-config" in str(exc.value)


def test_yaml_loader_bad_top_level(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("- a\n", encoding="utf-8")
    with pytest.raises(ValueError, match="顶层必须是字典"):
        YAMLLoader().load(p)


def test_load_yaml_source_maps_exceptions(tmp_path):
    with pytest.raises(ConfigFileNotFoundError):
        load_yaml_source(tmp_path / "missing.yaml", "train")


def test_cli_loader_namespace():
    args = Namespace(epochs=50, help="x", verbose=None, _private=1)
    cfg = CLILoader().load(args)
    assert cfg == {"epochs": 50}


def test_cli_loader_mapping():
    cfg = CLILoader(mapping={"learning_rate": "lr0"}).load({"learning_rate": 0.01})
    assert cfg == {"lr0": 0.01}


def test_load_all_sources(tmp_path):
    y = tmp_path / "train.yaml"
    y.write_text("epochs: 30\n", encoding="utf-8")
    out = load_all_sources(
        yaml_path=y,
        cli_args={"epochs": 10, "task": "train"},
    )
    assert out["yaml"]["epochs"] == 30
    assert "task" not in out["cli"]
    assert out["cli"]["epochs"] == 10


def test_load_all_sources_yaml_parse_error(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("key: [unclosed", encoding="utf-8")
    with pytest.raises(ValueError, match="YAML"):
        load_all_sources(yaml_path=p)
