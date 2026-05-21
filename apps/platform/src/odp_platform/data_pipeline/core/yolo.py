# -*- coding: utf-8 -*-
"""YOLO 直通 converter。"""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import List

from odp_platform.common.constants import AnnotationFormat, Task
from odp_platform.data_pipeline.registry import ConvertOptions, register

logger = logging.getLogger(__name__)


@register(AnnotationFormat.YOLO, supported_tasks=(Task.DETECT,))
def passthrough_yolo(
    input_dir: Path,
    output_labels_dir: Path,
    options: ConvertOptions,
) -> List[str]:
    if not options.classes:
        raise ValueError("YOLO 格式必须通过 options.classes 显式提供类别名")

    txt_files = sorted(input_dir.rglob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"YOLO 直通: 在 {input_dir} 下未找到 .txt")

    output_labels_dir.mkdir(parents=True, exist_ok=True)
    use_hardlink = _supports_hardlink(input_dir, output_labels_dir)

    for txt in txt_files:
        dst = output_labels_dir / txt.name
        if dst.exists():
            dst.unlink()
        if use_hardlink:
            try:
                os.link(txt, dst)
                continue
            except OSError:
                pass
        shutil.copy2(txt, dst)

    return list(options.classes)


def _supports_hardlink(src_dir: Path, dst_dir: Path) -> bool:
    try:
        return src_dir.stat().st_dev == dst_dir.stat().st_dev
    except OSError:
        return False
