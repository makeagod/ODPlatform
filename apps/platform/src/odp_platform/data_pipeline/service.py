# -*- coding: utf-8 -*-
"""数据流水线业务调度层。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from odp_platform.data_pipeline.registry import ConvertOptions, get_converter, list_capabilities


def get_pipeline_capabilities() -> Dict[str, Tuple[str, ...]]:
    return list_capabilities()


def convert_data_to_yolo(
    input_dir: Path,
    output_labels_dir: Path,
    annotation_format: str,
    options: ConvertOptions,
) -> List[str]:
    entry = get_converter(annotation_format)
    if not entry.supports(options.task):
        raise ValueError(
            f"格式 {annotation_format!r} 不支持 task={options.task!r}, "
            f"支持: {entry.supported_tasks}"
        )
    return entry.func(input_dir, output_labels_dir, options)
