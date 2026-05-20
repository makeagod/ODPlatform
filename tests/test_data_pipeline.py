# -*- coding: utf-8 -*-
"""
阶段 10: 数据准备流水线自动化单元测试
"""
import pytest
from pathlib import Path
from odp_platform.data_pipeline.split.manifest import DatasetManifest, SampleItem
from odp_platform.data_pipeline.split.splitter import DatasetSplitter


def test_dataset_splitter_precision_and_logic():
    """验证智能切分器在标准比例和浮点数边界下的切分精密性"""
    # 1. 构造一个包含 10 张模拟图片的元数据清单
    manifest = DatasetManifest()
    for i in range(10):
        item = SampleItem(
            image_path=Path(f"mock_img_{i}.jpg"),
            annotations=[{"category": "car", "bbox": [0, 0, 10, 10]}],
            width=100,
            height=100,
            raw_format="pascal_voc"
        )
        manifest.add_item(item)

    # 2. 初始化切分器 (7:2:1)
    splitter = DatasetSplitter(train_ratio=0.7, val_ratio=0.2, test_ratio=0.1)
    train, val, test = splitter.split(manifest)

    # 3. 断言数量严格对齐
    assert len(train) == 7
    assert len(val) == 2
    assert len(test) == 1
    assert len(train) + len(val) + len(test) == 10


def test_dataset_splitter_invalid_ratio():
    """验证当切分比例之和不等于 1.0 时，系统是否能 Fail-Fast 抛出异常"""
    with pytest.raises(ValueError) as exc_info:
        # 0.6 + 0.2 + 0.1 = 0.9 != 1.0
        DatasetSplitter(train_ratio=0.6, val_ratio=0.2, test_ratio=0.1)

    assert "数据集切分比例之和必须为 1.0" in str(exc_info.value)