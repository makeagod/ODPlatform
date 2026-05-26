#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""朴素 YOLO 训练示例（教程对照，不进平台编排）。

对比 D6：请使用 ``odp-train`` + ``TrainService``。
"""
from __future__ import annotations

import argparse

from ultralytics import YOLO

from odp_platform.common.dataset_path import resolve_dataset_path
from odp_platform.common.model_path import resolve_model_path
from odp_platform.common.paths import dataset_yaml_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="YOLO 训练 (朴素版)")
    parser.add_argument("--model", type=str, default="yolo11n.pt")
    parser.add_argument(
        "--data",
        type=str,
        default=str(dataset_yaml_path("rsod")),
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", type=str, default="0")
    parser.add_argument("--lr0", type=float, default=0.01)
    parser.add_argument("--optimizer", type=str, default="auto")
    parser.add_argument("--workers", type=int, default=8)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    model_path = resolve_model_path(args.model)
    data_path = resolve_dataset_path(args.data)

    model = YOLO(str(model_path))
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        lr0=args.lr0,
        optimizer=args.optimizer,
        workers=args.workers,
    )
    print(results)


if __name__ == "__main__":
    main()
