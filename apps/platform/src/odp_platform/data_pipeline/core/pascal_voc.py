# -*- coding: utf-8 -*-
"""PASCAL VOC XML → YOLO txt converter。"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

from odp_platform.common.constants import AnnotationFormat, Task
from odp_platform.data_pipeline.registry import ConvertOptions, register

logger = logging.getLogger(__name__)


@register(AnnotationFormat.PASCAL_VOC, supported_tasks=(Task.DETECT,))
def convert_voc(
    input_dir: Path,
    output_labels_dir: Path,
    options: ConvertOptions,
) -> List[str]:
    xml_files = sorted(input_dir.rglob("*.xml"))
    if not xml_files:
        raise FileNotFoundError(f"在 {input_dir} 下未找到任何 XML")

    output_labels_dir.mkdir(parents=True, exist_ok=True)
    classes: List[str] = list(options.classes) if options.classes else []
    auto_discover = not options.classes

    n_ok = n_skip = 0
    for xml_path in xml_files:
        if _convert_one(xml_path, output_labels_dir, classes, auto_discover):
            n_ok += 1
        else:
            n_skip += 1

    logger.info(f"VOC 转换完成: {n_ok} 成功, {n_skip} 跳过, 类别 {len(classes)} 种")
    return classes


def _convert_one(
    xml_path: Path,
    output_labels_dir: Path,
    classes: List[str],
    auto_discover: bool,
) -> bool:
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as e:
        logger.warning(f"{xml_path.name} XML 损坏: {e}")
        return False

    size = root.find("size")
    if size is None:
        return False
    w = float(size.findtext("width", "0"))
    h = float(size.findtext("height", "0"))
    if w <= 0 or h <= 0:
        return False

    lines: List[str] = []
    for obj in root.findall("object"):
        name = obj.findtext("name")
        if not name:
            continue
        if name not in classes:
            if auto_discover:
                classes.append(name)
            else:
                continue
        cls_id = classes.index(name)

        bbox = obj.find("bndbox")
        if bbox is None:
            continue
        try:
            xmin = float(bbox.findtext("xmin"))
            ymin = float(bbox.findtext("ymin"))
            xmax = float(bbox.findtext("xmax"))
            ymax = float(bbox.findtext("ymax"))
        except (TypeError, ValueError):
            continue

        cx = max(0.0, min(1.0, (xmin + xmax) / 2 / w))
        cy = max(0.0, min(1.0, (ymin + ymax) / 2 / h))
        bw = max(0.0, min(1.0, (xmax - xmin) / w))
        bh = max(0.0, min(1.0, (ymax - ymin) / h))
        lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

    out_txt = output_labels_dir / f"{xml_path.stem}.txt"
    out_txt.write_text("\n".join(lines), encoding="utf-8")
    return True
