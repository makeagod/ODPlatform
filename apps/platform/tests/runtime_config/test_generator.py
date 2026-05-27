# -*- coding: utf-8 -*-
"""odp-gen-config / ConfigGenerator 测试。"""
from __future__ import annotations

import subprocess
import sys

from odp_platform.runtime_config.generator import (
    ConfigGenerator,
    cli_name_to_task_kind,
    main,
)


def test_cli_name_to_task_kind_infer_maps_predict():
    assert cli_name_to_task_kind("infer") == "predict"


def test_generator_writes_train_yaml(tmp_path):
    out = tmp_path / "train.yaml"
    ok = ConfigGenerator().generate("train", out, overwrite=True)
    assert ok is True
    assert out.exists()
    assert "epochs:" in out.read_text(encoding="utf-8")


def test_generator_skips_existing_without_overwrite(tmp_path):
    out = tmp_path / "val.yaml"
    out.write_text("task: detect\n", encoding="utf-8")
    ok = ConfigGenerator().generate("val", out, overwrite=False)
    assert ok is False
    assert out.read_text(encoding="utf-8") == "task: detect\n"


def test_main_subcommand_train(tmp_path):
    out = tmp_path / "train.yaml"
    rc = main(["train", "-o", str(out), "--overwrite"])
    assert rc == 0
    assert out.exists()


def test_python_m_module_smoke(tmp_path):
    out = tmp_path / "val.yaml"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "odp_platform.runtime_config.generator",
            "val",
            "-o",
            str(out),
            "--overwrite",
        ],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    assert "已生成" in result.stdout
