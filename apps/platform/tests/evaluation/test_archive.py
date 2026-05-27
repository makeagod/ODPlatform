# -*- coding: utf-8 -*-
from pathlib import Path

from odp_platform.evaluation.archive import archive_val_results


def test_archive_val_results_creates_metrics_json(tmp_path):
    val_dir = tmp_path / "val_output"
    val_dir.mkdir()
    (val_dir / "coco_metrics.json").write_text('{"mAP50": 0.95}', encoding="utf-8")

    archive_dir = tmp_path / "archive"
    result = archive_val_results(val_dir, "best.pt", archive_dir=archive_dir)

    assert result["metrics_json"] is not None
    assert result["metrics_json"].exists()
    content = result["metrics_json"].read_text()
    assert "mAP50" in content


def test_archive_val_results_missing_source(tmp_path):
    val_dir = tmp_path / "empty_val"
    val_dir.mkdir()
    archive_dir = tmp_path / "archive"
    result = archive_val_results(val_dir, "best.pt", archive_dir=archive_dir)
    assert result["metrics_json"] is None
    assert result["confusion_matrix"] is None
