#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : init_project.py
# @Time      : 2026/5/18 11:34:37
# @Author    : 雨霓同学
# @Project   : ODPlatform
# @Function  : 项目初始化脚本，自动创建所需的17个核心目录结构

import logging
import sys
from pathlib import Path
from typing import List

# ============================================================
# 🌟 动态路标：无论在哪个环境运行，强行把 src 目录加进 Python 大脑
# ============================================================
current_file = Path(__file__).resolve()
src_dir = current_file.parents[2]
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 引入项目底层三大基础设施工具 (确保你的文件夹名字叫 common)
from odp_platform.logging import setup_cli_logging
from odp_platform.common.string_utils import format_table_row, format_table_separator
from odp_platform.common.performance_utils import time_it
from odp_platform.common.paths import ROOT_DIR, RAW_DATA_DIR, get_dirs_to_initialize

LINE_WIDTH = 60
logger = logging.getLogger(__name__)


def _check_raw_data_status() -> List[str]:
    """检查raw_data目录的状况"""
    raw_status: List[str] = []
    rel_raw = RAW_DATA_DIR.relative_to(ROOT_DIR)

    if not RAW_DATA_DIR.exists():
        logger.warning(f"检测到原始数据集目录不存在: [{RAW_DATA_DIR}] \n"
                       f"  请在项目初始化完成后【手动创建】命名该文件夹")
        raw_status.append(f"[{rel_raw}] 不存在 -> 待创建并放入原始数据")
    elif not any(RAW_DATA_DIR.iterdir()):
        logger.warning(f"检测到原始数据集目录为空: [{RAW_DATA_DIR}] \n"
                       f"  请延迟将数据子集存入:\n"
                       f"    ├── {rel_raw} / images / \n"
                       f"    └──             annotations /")
        raw_status.append(f"[{rel_raw}] 为空 -> 存放人至少一个有效子集")
    else:
        sub_dirs = [d for d in RAW_DATA_DIR.iterdir() if d.is_dir()]
        logger.info(f"检测到原始数据集目录下有 {len(sub_dirs)} 个子集文件夹")
        raw_status.append(f"数据目录 [{len(sub_dirs)}] 个有效子集")
        for sub in sorted(sub_dirs):
            raw_status.append(f"  包含子集: {sub.name}")

    return raw_status


@time_it(iterations=1, name="项目初始化", logger_instance=logger)
def initialize_project() -> None:
    """
    初始化项目，创建开头所有的目录
    :return: None
    """
    # 优先装配并启动日志系统
    setup_cli_logging("init_project")

    logger.info(f"{' 开始初始化项目结构 ':#^{LINE_WIDTH}}")
    logger.info(f"当前项目根目录: {ROOT_DIR}")

    created: List[Path] = []
    existed: List[Path] = []

    # 循环遍历 17 个待初始化的标准文件夹
    for d in get_dirs_to_initialize():
        rel = d.relative_to(ROOT_DIR)
        if d.exists():
            logger.info(f"目录已存在: {rel}")
            existed.append(d)
        else:
            try:
                d.mkdir(parents=True, exist_ok=True)
                logger.info(f"成功创建新目录: {rel}")
                created.append(d)
            except OSError as e:
                logger.error(f"创建目录失败: [{rel}] : {e}")
                raise SystemExit(1) from e

    # 检查原始数据集状态
    logger.info(f"{' 检查原始数据集状态 ':#^{LINE_WIDTH}}")
    raw_status = _check_raw_data_status()

    # 打印最终的汇总审计小表格
    logger.info(f"{' 结构初始化审计报告汇总 ':#^{LINE_WIDTH}}")
    widths = [38, 12]
    aligns = ["left", "right"]
    logger.info(format_table_row(['检查项', '状态'], widths, aligns))
    logger.info(format_table_separator(widths))

    for d in created:
        logger.info(format_table_row([str(d.relative_to(ROOT_DIR)), '成功创建'], widths, aligns))
    for d in existed:
        logger.info(format_table_row([str(d.relative_to(ROOT_DIR)), '已存在'], widths, aligns))

    logger.info("=" * LINE_WIDTH)


def main() -> None:
    """CLI 入口 (odp-init)。"""
    initialize_project()


if __name__ == "__main__":
    main()