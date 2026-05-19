#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :init_project.py
# @Time      :2026/5/18 11:34:37
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :
from pathlib import Path
from typing import List

from odp_platform.common.paths import ROOT_DIR, get_dirs_to_initialize


def initialize_project() -> None:
    """
    初始化项目，创建所有必要的目录
    :return: None
    """
    print("=" * 60)
    print(f"开始初始化项目...项目根路径为: {ROOT_DIR}")
    print("=" * 60)

    created: List[Path] = []
    existed: List[Path] = []

    for d in get_dirs_to_initialize():
        rel = d.relative_to(ROOT_DIR)
        if d.exists():
            print(f"  - {rel} 已存在")
            existed.append(d)
        else:
            d.mkdir(parents=True, exist_ok=True)
            print(f"  - {rel} 创建成功")
            created.append(d)
    print("-" * 60)
    print(f"初始化完成，共创建了 {len(created)} 个目录，已经存在的目录有 {len(existed)} 个")
    print("-" * 60)


if __name__ == "__main__":
    initialize_project()