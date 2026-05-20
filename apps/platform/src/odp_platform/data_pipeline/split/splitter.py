# -*- coding: utf-8 -*-
"""
阶段 5: 数据集智能切分器 (带浮点数余数最大化分配算法)
"""
import math
import random
from typing import List, Tuple
from odp_platform.data_pipeline.split.manifest import DatasetManifest, SampleItem


class DatasetSplitter:
    """将总清单按比例切分为三大子集的计算器"""

    def __init__(self, train_ratio: float = 0.7, val_ratio: float = 0.2, test_ratio: float = 0.1,
                 random_state: int = 42):
        if not math.isclose(train_ratio + val_ratio + test_ratio, 1.0, rel_tol=1e-9):
            raise ValueError(f"数据集切分比例之和必须为 1.0，当前: {train_ratio} + {val_ratio} + {test_ratio}")

        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.random_state = random_state

    def split(self, manifest: DatasetManifest) -> Tuple[List[SampleItem], List[SampleItem], List[SampleItem]]:
        """执行切分计算"""
        items = manifest.get_all_items()
        total_count = len(items)
        if total_count == 0:
            return [], [], []

        # 浅拷贝并使用固定随机种子打乱顺序，确保结果可复现
        shuffled_items = list(items)
        random.seed(self.random_state)
        random.shuffle(shuffled_items)

        # 1. 基础分配（直接取整）
        train_count = int(total_count * self.train_ratio)
        val_count = int(total_count * self.val_ratio)
        test_count = int(total_count * self.test_ratio)

        # 2. 余数分配（最大余数法，防止因为取整漏掉样本）
        allocated = train_count + val_count + test_count
        remainder = total_count - allocated

        if remainder > 0:
            # 计算各自的小数点残余
            diffs = [
                ("train", (total_count * self.train_ratio) - train_count),
                ("val", (total_count * self.val_ratio) - val_count),
                ("test", (total_count * self.test_ratio) - test_count),
            ]
            # 按小数残余从大到小排序
            diffs.sort(key=lambda x: x[1], reverse=True)

            # 将多出来的样本依次分给残余最大的子集
            for i in range(remainder):
                split_name = diffs[i][0]
                if split_name == "train":
                    train_count += 1
                elif split_name == "val":
                    val_count += 1
                elif split_name == "test":
                    test_count += 1

        # 3. 按照计算好的精确边界切分数组
        train_end = train_count
        val_end = train_count + val_count

        train_items = shuffled_items[:train_end]
        val_items = shuffled_items[train_end:val_end]
        test_items = shuffled_items[val_end:]

        return train_items, val_items, test_items