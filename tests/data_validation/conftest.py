# -*- coding: utf-8 -*-
from pathlib import Path

import pytest
import yaml

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def healthy_yaml(tmp_path: Path) -> Path:
    root = tmp_path / "ds"
    for split in ("train", "val"):
        (root / split / "images").mkdir(parents=True)
        (root / split / "labels").mkdir(parents=True)
        img = root / split / "images" / f"a_{split}.jpg"
        img.write_bytes(b"\xff\xd8\xff")
        lbl = root / split / "labels" / f"a_{split}.txt"
        lbl.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    cfg = {
        "path": str(root.resolve()),
        "train": "train/images",
        "val": "val/images",
        "nc": 1,
        "names": ["cat"],
        "task": "detect",
    }
    yaml_path = tmp_path / "healthy.yaml"
    yaml_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return yaml_path


@pytest.fixture
def bad_nc_names_yaml(tmp_path: Path) -> Path:
    cfg = {"nc": 3, "names": ["a", "b"]}
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p
