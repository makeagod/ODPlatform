# -*- coding: utf-8 -*-
"""
阶段 5: 数据集样本清单实体定义
"""
import dataclasses
from pathlib import Path
from typing import List, Dict, Any


@dataclasses.dataclass
class SampleItem:
    """单个图片样本的标准化元数据"""
    # 原始图片的绝对路径
    image_path: Path
    # 对应的标准化标注数据（包含类别与绝对坐标 bbox）
    annotations: List[Dict[str, Any]]
    # 图片的宽、高
    width: int
    # 标注对应的原始格式（如 pascal_voc）
    raw_format: str


class DatasetManifest:
    """由多个 SampleItem 组成的数据集样本总清单"""
    def __init__(self, items: List[SampleItem] = None):
        self.items = items or []

    def add_item(self, item: SampleItem):
        self.items.append(item)

    @property
    def size(self) -> int:
        return len(self.items)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """转换为可序列化的字典列表，方便流式中转"""
        return [dataclasses.asdict(item) for item in self.items]