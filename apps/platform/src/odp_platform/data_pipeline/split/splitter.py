# -*- coding: utf-8 -*-
"""数据集智能切分器。"""
from __future__ import annotations

import random
from typing import List

from odp_platform.data_pipeline.split.manifest import PairList, SplitManifest

RATE_EPSILON = 1e-9


def split_pairs(
    pairs: PairList,
    train_rate: float,
    val_rate: float,
    test_rate: float | None = None,
    random_state: int = 42,
) -> SplitManifest:
    """
    将 (image, label) 对按比例切分为 train / val / test。

    :param train_rate: 训练集比例
    :param val_rate: 验证集比例
    :param test_rate: 测试集比例; 为 None 时自动取 1 - train_rate - val_rate
    """
    if test_rate is None:
        test_rate = 1.0 - train_rate - val_rate

    total_rate = train_rate + val_rate + test_rate
    if total_rate > 1.0 + RATE_EPSILON:
        raise ValueError(
            f"切分比例之和不能超过 1.0, 当前: {train_rate}+{val_rate}+{test_rate}"
        )
    if train_rate < 0 or val_rate < -RATE_EPSILON or test_rate < -RATE_EPSILON:
        raise ValueError("切分比例不能为负")

    n = len(pairs)
    manifest = SplitManifest(
        train_rate=train_rate,
        val_rate=val_rate,
        test_rate=max(test_rate, 0.0),
        random_state=random_state,
    )

    if n == 0:
        return manifest

    if n < 3:
        manifest.train = list(pairs)
        return manifest

    shuffled = list(pairs)
    rng = random.Random(random_state)
    rng.shuffle(shuffled)

    train_n = int(n * train_rate)
    val_n = int(n * val_rate)
    test_n = int(n * test_rate)

    allocated = train_n + val_n + test_n
    remainder = n - allocated
    if remainder > 0:
        diffs = [
            ("train", n * train_rate - train_n),
            ("val", n * val_rate - val_n),
            ("test", n * test_rate - test_n),
        ]
        diffs.sort(key=lambda x: x[1], reverse=True)
        for i in range(remainder):
            name = diffs[i][0]
            if name == "train":
                train_n += 1
            elif name == "val":
                val_n += 1
            else:
                test_n += 1

    if test_rate <= RATE_EPSILON:
        test_n = 0

    if val_rate <= RATE_EPSILON:
        val_n = 0
        test_n = n - train_n

    train_end = min(train_n, n)
    val_end = min(train_end + val_n, n)

    manifest.train = shuffled[:train_end]
    manifest.val = shuffled[train_end:val_end]
    manifest.test = shuffled[val_end:val_end + test_n]

    return manifest
