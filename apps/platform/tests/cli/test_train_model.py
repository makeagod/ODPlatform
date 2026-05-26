# -*- coding: utf-8 -*-
from odp_platform.cli.train_model import build_parser


def test_odp_train_parser_accepts_course_examples():
    p = build_parser()
    args_cpu = p.parse_args(
        [
            "--epochs",
            "3",
            "--batch",
            "8",
            "--device",
            "cpu",
            "--model",
            "yolov8n.pt",
            "--data",
            "rsod.yaml",
        ]
    )
    assert args_cpu.epochs == 3
    assert args_cpu.batch == 8
    assert args_cpu.device == "cpu"
    assert args_cpu.model == "yolov8n.pt"
    assert args_cpu.data == "rsod.yaml"

    args_gpu = p.parse_args(
        ["--epochs", "3", "--batch", "8", "--device", "0", "--model", "yolov8n.pt", "--data", "rsod.yaml"]
    )
    assert args_gpu.device == "0"
