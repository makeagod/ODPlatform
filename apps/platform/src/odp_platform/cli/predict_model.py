# -*- coding: utf-8 -*-
"""odp-predict — YOLO 推理命令行入口。"""
from __future__ import annotations

import argparse
import logging
import sys

from odp_platform.common.paths import runtime_config_path
from odp_platform.frame_source import CameraConfig
from odp_platform.inference.service import InferService
from odp_platform.logging import setup_cli_logging

_CONFIG_KEYS = frozenset({
    "model", "source", "data", "imgsz", "batch", "device", "conf", "iou",
    "max_det", "classes", "agnostic_nms", "augment", "vid_stride",
    "stream", "stream_buffer", "save", "save_txt", "save_conf", "save_crop",
    "save_frames", "show", "show_labels", "show_conf", "show_boxes",
    "line_width", "project", "name", "exist_ok", "verbose", "half",
    "retina_masks", "visualize", "embed", "experiment_name",
})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odp-predict",
        description="YOLO 推理 — D5 配置 + frame_source + ultralytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  odp-predict --model best.pt --source 0 --show\n"
            "  odp-predict --source image.jpg --model yolov8n.pt\n"
            "  odp-predict --source ./images/ --model best.pt --save-txt\n"
            "  odp-predict --yaml configs/runtime/infer.yaml\n"
            "\n"
            "提示: 若 infer.yaml 尚未生成, 先跑 `odp-gen-config infer`."
        ),
    )

    parser.add_argument(
        "--yaml", dest="yaml_path", type=str, default=None,
        help="推理配置 YAML（默认 configs/runtime/infer.yaml）",
    )
    parser.add_argument("--model", type=str, help="模型权重")
    parser.add_argument(
        "--source", type=str,
        help="输入源: 0=摄像头 / 视频 / 图片 / 目录",
    )
    parser.add_argument("--imgsz", type=int, help="推理图像尺寸")
    parser.add_argument("--batch", type=int, help="batch size")
    parser.add_argument("--device", type=str, help="设备 0 / cpu")
    parser.add_argument("--conf", type=float, help="置信度阈值")
    parser.add_argument("--iou", type=float, help="NMS IoU")
    parser.add_argument("--max-det", dest="max_det", type=int)
    parser.add_argument("--vid-stride", dest="vid_stride", type=int, help="每 N 帧推理一次")
    parser.add_argument("--project", type=str, help="输出根目录")
    parser.add_argument("--name", type=str, help="运行子目录名")

    parser.add_argument("--show", action="store_true", help="弹窗显示")
    parser.add_argument("--save-txt", dest="save_txt", action="store_true")
    parser.add_argument(
        "--no-save",
        dest="save",
        action="store_false",
        default=None,
        help="不保存标注图像",
    )

    parser.add_argument("--camera-width", dest="camera_width", type=int)
    parser.add_argument("--camera-height", dest="camera_height", type=int)
    parser.add_argument("--camera-fps", dest="camera_fps", type=int)
    parser.add_argument("--camera-backend", dest="camera_backend", type=str)
    parser.add_argument("--camera-codec", dest="camera_codec", type=str)
    parser.add_argument(
        "--threaded",
        action="store_true",
        help="强制线程化采集（摄像头默认开启）",
    )
    parser.add_argument(
        "--no-threaded", dest="threaded", action="store_false",
        help="禁用线程化采集",
    )
    parser.set_defaults(threaded=None)
    parser.add_argument("--warmup-frames", dest="warmup_frames", type=int, default=30)
    parser.add_argument("--max-frames", dest="max_frames", type=int, default=None)
    parser.add_argument("--no-rename-log", dest="rename_log", action="store_false")
    parser.set_defaults(rename_log=True)
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    setup_cli_logging("predict", log_level=getattr(logging, args.log_level))

    cli_args = {
        k: v for k, v in vars(args).items()
        if k in _CONFIG_KEYS and v is not None
    }

    cam_cfg = None
    if any(
        getattr(args, k) is not None
        for k in ("camera_width", "camera_height", "camera_fps", "camera_backend", "camera_codec")
    ):
        cam_kwargs: dict = {}
        if args.camera_width is not None:
            cam_kwargs["width"] = args.camera_width
        if args.camera_height is not None:
            cam_kwargs["height"] = args.camera_height
        if args.camera_fps is not None:
            cam_kwargs["fps"] = args.camera_fps
        if args.camera_backend is not None:
            cam_kwargs["backend"] = args.camera_backend
        if args.camera_codec is not None:
            cam_kwargs["codec"] = args.camera_codec
        cam_cfg = CameraConfig(**cam_kwargs)

    yaml_path = args.yaml_path or runtime_config_path("infer")

    try:
        result = InferService().predict(
            yaml_path=yaml_path,
            cli_args=cli_args,
            camera_config=cam_cfg,
            use_threaded=args.threaded,
            warmup_frames=args.warmup_frames,
            max_frames=args.max_frames,
            rename_log=args.rename_log,
        )
    except KeyboardInterrupt:
        print("\n用户中断推理.", file=sys.stderr)
        return 130

    if result.success:
        print(f"推理完成, 处理 {result.frames_processed} 帧, 输出: {result.output_dir}")
        return 0

    print(f"推理失败: {result.error}", file=sys.stderr)
    if result.log_path:
        print(f"   详见日志: {result.log_path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
