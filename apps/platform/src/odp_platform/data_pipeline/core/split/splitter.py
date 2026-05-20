# -*- coding: utf-8 -*-
"""
阶段 5: 基于比例的数据集切分策略器
"""
import random
from typing import Tuple, List
from odp_platform.data_pipeline.split.manifest import DatasetManifest, SampleItem

# 浮点数精度误差容忍上限
RATE_EPSILON = 1e-6


class DatasetSplitter:
    """将总清单按比例切分为三大子集的计算器"""

    def __init__(self, train_ratio: float = 0.7, val_ratio: float = 0.2, test_ratio: float = 0.1,
                 random_state: int = 42):
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.random_state = random_state

        # 🚀 边界判断：比例之和必须精密等于 1.0
        total_ratio = train_ratio + val_ratio + test_ratio
        if abs(total_ratio - 1.0) > RATE_EPSILON:
            raise ValueError(
                f"数据集切分比例之和必须为 1.0! 当前 train({train_ratio}) + val({val_ratio}) + test({test_ratio}) = {total_ratio}"
            )

    def split(self, manifest: DatasetManifest) -> Tuple[List[SampleItem], List[SampleItem], List[SampleItem]]:
        """
        执行切分计算
        :return: (train_items, val_items, test_items)
        """
        items = list(manifest.items)
        if not items:
            return [], [], []

        # 锁定随机种子，确保每次运行切分出来的图片一模一样（可复现性）
        random.seed(self.random_state)
        random.shuffle(items)

        total_count = len(items)

        # 精准计算切分边界索引
        train_end = int(total_count * self.train_ratio)
        val_end = train_end + int(total_count * self.val_ratio)

        # 兜底截断，防止由于向下取整导致最后漏掉样本
        train_items = items[:train_end]
        val_items = items[train_end:val_end]
        test_items = items[val_end:]

        # 如果切分出来结果全为空，触发警告
        if total_count > 0 and not train_items:
            # 至少分一张给训练集
            train_items = [items[0]]
            val_items = items[1:val_end]

        return train_items, val_items, test_items