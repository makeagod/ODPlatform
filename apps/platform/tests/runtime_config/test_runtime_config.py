# -*- coding: utf-8 -*-
import pytest
import yaml

from odp_platform.runtime_config import (
    ConfigFileNotFoundError,
    ConfigValidationError,
    UnknownFieldError,
    build_train_config,
    generate_config_template,
)
from odp_platform.runtime_config.builder import build_config
from odp_platform.runtime_config.exceptions import ConfigParseError
from odp_platform.runtime_config.sources import load_yaml_source


def test_ac01_defaults_only():
    cfg = build_train_config()
    assert cfg.values["epochs"] == 100
    assert cfg.provenance.current_source("epochs") == "defaults"


def test_ac02_yaml_overrides(tmp_path):
    y = tmp_path / "train.yaml"
    y.write_text("epochs: 50\nbatch: 8\n", encoding="utf-8")
    cfg = build_train_config(yaml_path=y)
    assert cfg.values["epochs"] == 50
    assert cfg.values["batch"] == 8
    assert cfg.provenance.current_source("epochs") == "yaml"


def test_ac03_cli_beats_yaml(tmp_path):
    y = tmp_path / "t.yaml"
    y.write_text("epochs: 50\n", encoding="utf-8")
    cfg = build_train_config(yaml_path=y, cli_overrides={"epochs": 3})
    assert cfg.values["epochs"] == 3
    assert cfg.provenance.current_source("epochs") == "cli"


def test_ac04_missing_yaml(tmp_path):
    missing = tmp_path / "nope.yaml"
    with pytest.raises(ConfigFileNotFoundError) as exc:
        build_train_config(yaml_path=missing)
    assert "odp-config-gen" in str(exc.value)
    assert str(missing.resolve()) in str(exc.value) or "不存在" in str(exc.value)


def test_ac05_yaml_list_top(tmp_path):
    y = tmp_path / "bad.yaml"
    y.write_text("- a\n", encoding="utf-8")
    with pytest.raises(ConfigParseError):
        load_yaml_source(y, "train")


def test_ac06_unknown_field(tmp_path):
    y = tmp_path / "t.yaml"
    y.write_text("epchs: 1\n", encoding="utf-8")
    with pytest.raises(UnknownFieldError):
        build_train_config(yaml_path=y)


def test_ac07_invalid_task(tmp_path):
    y = tmp_path / "t.yaml"
    y.write_text("task: detection_wrong\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError) as exc:
        build_train_config(yaml_path=y)
    assert "experiment_id" in str(exc.value)


def test_ac08_validation_with_provenance(tmp_path):
    y = tmp_path / "t.yaml"
    y.write_text("batch: 0\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError) as exc:
        build_train_config(yaml_path=y)
    assert "溯源" in str(exc.value) or "batch" in str(exc.value)


def test_ac09_contradictory_save(tmp_path):
    y = tmp_path / "t.yaml"
    y.write_text("save: false\nsave_period: 5\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError):
        build_train_config(yaml_path=y)


def test_ac10_redundant_warn(tmp_path):
    y = tmp_path / "t.yaml"
    y.write_text("mosaic: 0.0\nclose_mosaic: 10\n", encoding="utf-8")
    cfg = build_train_config(yaml_path=y)
    assert any("mosaic" in w for w in cfg.warnings)


def test_ac11_falsey_override(tmp_path):
    y = tmp_path / "t.yaml"
    y.write_text("verbose: true\n", encoding="utf-8")
    cfg = build_train_config(yaml_path=y, cli_overrides={"verbose": False})
    assert cfg.values["verbose"] is False


def test_ac12_generate_template(tmp_path):
    out = tmp_path / "train.yaml"
    generate_config_template("train", out, force=True)
    text = out.read_text(encoding="utf-8")
    assert "epochs" in text
    assert "# " in text


def test_ac13_template_loadable(tmp_path):
    out = tmp_path / "train.yaml"
    generate_config_template("train", out, force=True)
    cfg = build_train_config(yaml_path=out)
    assert cfg.values["epochs"] == 100


def test_ac14_skip_existing(tmp_path):
    out = tmp_path / "train.yaml"
    out.write_text("epochs: 99\n", encoding="utf-8")
    generate_config_template("train", out, force=False)
    assert "epochs: 99" in out.read_text(encoding="utf-8")


def test_ac15_force_backup(tmp_path):
    out = tmp_path / "train.yaml"
    out.write_text("epochs: 99\n", encoding="utf-8")
    generate_config_template("train", out, force=True, backup=True)
    backups = list(tmp_path.glob("train.yaml.bak.*"))
    assert backups
    assert "epochs: 100" in out.read_text(encoding="utf-8") or yaml.safe_load(out.read_text())["epochs"] == 100


def test_ac16_provenance_chain(tmp_path):
    y = tmp_path / "t.yaml"
    y.write_text("epochs: 50\n", encoding="utf-8")
    cfg = build_train_config(yaml_path=y, cli_overrides={"epochs": 10})
    chain = cfg.provenance.chains["epochs"]
    assert len(chain) >= 3
    assert cfg.provenance.to_dict()["epochs"]


def test_ac17_snapshot_roundtrip():
    cfg = build_train_config(cli_overrides={"epochs": 12})
    snap = cfg.snapshot()
    restored = build_config(
        snap["task_kind"],
        extra_layers=[("snapshot", snap["values"])],
        source_priority=["defaults", "snapshot"],
    )
    assert restored.values["epochs"] == 12


def test_ac19_preview_skips_validation(tmp_path):
    y = tmp_path / "t.yaml"
    y.write_text("batch: 0\n", encoding="utf-8")
    cfg = build_train_config(yaml_path=y, preview_only=True)
    assert cfg.values["batch"] == 0


def test_ac20_ultralytics_kwargs():
    cfg = build_train_config()
    kw = cfg.to_backend_kwargs("ultralytics")
    assert "experiment_id" not in kw
    assert "epochs" in kw


def test_ac21_mmdetection_adapter():
    cfg = build_train_config(cli_overrides={
        "epochs": 50, "batch": 8, "lr0": 0.001, "seed": 42,
        "imgsz": 640, "workers": 4, "patience": 10,
        "project": "runs/mmdet", "name": "exp_01",
    })
    kw = cfg.to_backend_kwargs("mmdetection")

    # 嵌套结构存在
    assert kw["train_dataloader"]["batch_size"] == 8
    assert kw["train_dataloader"]["num_workers"] == 4
    assert kw["val_dataloader"]["batch_size"] == 8
    assert kw["optim_wrapper"]["optimizer"]["lr"] == 0.001
    assert kw["optim_wrapper"]["optimizer"]["type"] == "SGD"
    assert kw["train_cfg"]["max_epochs"] == 50
    assert kw["randomness"]["seed"] == 42
    assert kw["train_pipeline"]["img_scale"] == (640, 640)
    assert kw["test_pipeline"]["img_scale"] == (640, 640)
    assert kw["work_dir"].replace("\\", "/") == "runs/mmdet/exp_01"

    # patience 映射为 early_stop_patience
    assert kw["param_scheduler"]["early_stop_patience"] == 10


def test_ac22_adapter_registry():
    from odp_platform.runtime_config.adapters import get_adapter, register_adapter

    # 内置适配器
    assert get_adapter("ultralytics").backend_name == "ultralytics"
    assert get_adapter("mmdetection").backend_name == "mmdetection"

    # 未知后端
    import pytest
    with pytest.raises(ValueError, match="未知后端类型"):
        get_adapter("nonexistent")

    # 自定义注册
    from odp_platform.runtime_config.adapters import BaseBackendAdapter

    class DummyAdapter(BaseBackendAdapter):
        @property
        def backend_name(self) -> str:
            return "dummy"

        def translate(self, runtime_config):
            return {"dummy": True}

    register_adapter("dummy", DummyAdapter())
    assert get_adapter("dummy").backend_name == "dummy"
