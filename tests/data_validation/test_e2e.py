# -*- coding: utf-8 -*-
import json
import shutil
from pathlib import Path

from odp_platform.data_validation.checks.split_uniqueness import validate_split_uniqueness
from odp_platform.data_validation.registry import CheckContext, CheckSeverity
from odp_platform.data_validation.service import validate_dataset
from odp_platform.data_validation.snapshot import build_snapshot


def test_validate_dataset_e2e_healthy(healthy_yaml, tmp_path):
    report = validate_dataset(
        yaml_path=healthy_yaml,
        run_dir=tmp_path / "run1",
        write_report=True,
    )
    assert report.exit_code == 0
    assert report.overall_severity == CheckSeverity.PASS
    assert len(report.results) >= 4
    assert any(r.name == "placeholder" for r in report.results)
    assert report.report_path is not None
    assert report.report_path.exists()
    payload = json.loads(report.report_path.read_text(encoding="utf-8"))
    assert payload["exit_code"] == 0


def test_split_uniqueness_detects_leak(healthy_yaml, tmp_path):
    snap = build_snapshot(healthy_yaml)
    train_img = snap.images_per_split["train"][0]
    val_dir = snap.data_root / "val" / "images"
    shutil.copy2(train_img, val_dir / train_img.name)

    snap2 = build_snapshot(healthy_yaml)
    ctx = CheckContext(yaml_path=healthy_yaml, snapshot=snap2)
    leak = validate_split_uniqueness(ctx)
    assert leak.severity == CheckSeverity.ERROR

    report = validate_dataset(
        yaml_path=healthy_yaml,
        run_dir=tmp_path / "run2",
        write_report=False,
    )
    assert report.exit_code == 2
    names = {r.name: r.severity for r in report.results}
    assert names["split_uniqueness"] == CheckSeverity.ERROR
    assert names["yaml_schema"] == CheckSeverity.PASS
