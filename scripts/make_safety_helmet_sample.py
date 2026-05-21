#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 safety_helmet 最小 Pascal VOC 样本，供 D3/D4 课程验收。"""
from __future__ import annotations

import sys
from pathlib import Path

# 允许从仓库根目录直接运行
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "apps" / "platform" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from odp_platform.common.paths import RAW_DATA_DIR  # noqa: E402

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

NUM_SAMPLES = 60
CLASSES = ("helmet", "head")


def _write_jpeg(path: Path, idx: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if Image is not None:
        img = Image.new("RGB", (64, 64), color=(idx * 3 % 255, 40, 80))
        img.save(path, format="JPEG")
        return
    # 无 Pillow 时的最小合法 JPEG 占位
    minimal = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
        b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
        b"\x1c $.\x27 ,#\x1c\x1c(7),01444\x1f\x27=9=82<.342\xff\xc0\x00\x0b\x08"
        b"\x00\x01\x00\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01"
        b"\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07"
        b"\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05"
        b"\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"
        b"\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18"
        b"\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87"
        b"\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7"
        b"\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7"
        b"\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6"
        b"\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08"
        b"\x01\x01\x00\x00?\x00\xfd\xfc\xa2\x8a(\x03\xff\xd9"
    )
    path.write_bytes(minimal)


def _write_voc_xml(path: Path, stem: str, cls: str, w: int = 64, h: int = 64) -> None:
    xmin, ymin, xmax, ymax = 8, 8, 40, 40
    xml = f"""<annotation>
  <filename>{stem}.jpg</filename>
  <size><width>{w}</width><height>{h}</height><depth>3</depth></size>
  <object>
    <name>{cls}</name>
    <bndbox><xmin>{xmin}</xmin><ymin>{ymin}</ymin><xmax>{xmax}</xmax><ymax>{ymax}</ymax></bndbox>
  </object>
</annotation>
"""
    path.write_text(xml, encoding="utf-8")


def main() -> None:
    root = RAW_DATA_DIR / "safety_helmet"
    img_dir = root / "JPEGImages"
    ann_dir = root / "Annotations"
    img_dir.mkdir(parents=True, exist_ok=True)
    ann_dir.mkdir(parents=True, exist_ok=True)

    for i in range(NUM_SAMPLES):
        stem = f"helmet_{i:04d}"
        cls = CLASSES[i % len(CLASSES)]
        _write_jpeg(img_dir / f"{stem}.jpg", i)
        _write_voc_xml(ann_dir / f"{stem}.xml", stem, cls)

    print(f"[OK] safety_helmet 样本已生成: {root}")
    print(f"     图像 {NUM_SAMPLES} 张 | 类别 {CLASSES}")
    print("下一步: odp-transform --dataset safety_helmet --format pascal_voc")


if __name__ == "__main__":
    main()
