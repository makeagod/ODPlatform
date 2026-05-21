# -*- coding: utf-8 -*-
"""划分结果的数据载体。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

Pair = Tuple[Path, Path]
PairList = List[Pair]


@dataclass
class SplitManifest:
    train: PairList = field(default_factory=list)
    val: PairList = field(default_factory=list)
    test: PairList = field(default_factory=list)

    train_rate: float = 0.0
    val_rate: float = 0.0
    test_rate: float = 0.0
    random_state: int = 0

    def summary(self) -> dict:
        return {
            "train": len(self.train),
            "val": len(self.val),
            "test": len(self.test),
            "total": len(self.train) + len(self.val) + len(self.test),
        }
