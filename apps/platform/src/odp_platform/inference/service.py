# -*- coding: utf-8 -*-
"""InferService — 编排 D5 配置 + frame_source 出帧 + ultralytics 推理。"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO

from odp_platform.common.config_log import log_effective_config, log_override_chains
from odp_platform.common.log_rename import rename_log_to_save_dir
from odp_platform.common.model_path import resolve_model_path
from odp_platform.common.paths import CHECKPOINTS_DIR, PRETRAINED_MODELS_DIR, RUNS_DIR
from odp_platform.frame_source import CameraConfig, create_frame_source, create_threaded_source
from odp_platform.frame_source.core.base import FrameSource
from odp_platform.runtime_config.infer_build import build_infer_config

logger = logging.getLogger(__name__)

# 由 frame_source / 服务层消费，不传给 ultralytics.predict
_FRAMEWORK_PREDICT_KEYS = frozenset({
    "source",
    "experiment_name",
    "task",
    "stream",
    "stream_buffer",
    "vid_stride",
    "show",
    "show_labels",
    "show_conf",
    "show_boxes",
    "line_width",
    "save_frames",
})


def _find_project_log_path() -> Path | None:
    import logging as _logging

    from odp_platform.logging.constants import ROOT_LOGGER_NAME

    root = _logging.getLogger(ROOT_LOGGER_NAME)
    for h in root.handlers:
        if isinstance(h, _logging.FileHandler):
            return Path(h.baseFilename)
    return None


def _is_camera_source(source: str) -> bool:
    return source.isdigit()


def _build_camera_config(
    camera_config: CameraConfig | None,
    source: str,
) -> CameraConfig | None:
    if not _is_camera_source(source):
        return None
    camera_id = int(source)
    if camera_config is None:
        return CameraConfig(camera_id=camera_id)
    return camera_config.model_copy(update={"camera_id": camera_id})


def _create_frame_source(
    source: str,
    *,
    camera_config: CameraConfig | None,
    use_threaded: bool | None,
    warmup_frames: int,
) -> FrameSource:
    threaded = use_threaded if use_threaded is not None else _is_camera_source(source)
    cam_cfg = _build_camera_config(camera_config, source)
    if threaded:
        return create_threaded_source(
            source,
            camera_config=cam_cfg,
            warmup_frames=warmup_frames,
        )
    return create_frame_source(source, camera_config=cam_cfg)


@dataclass(frozen=True)
class InferResult:
    success: bool
    output_dir: Path
    frames_processed: int = 0
    infer_time: float | None = None
    error: str | None = None
    audit_path: Path | None = None
    log_path: Path | None = None


class InferService:
    """YOLO 推理编排：D5 配置 + frame_source 统一出帧。"""

    def predict(
        self,
        yaml_path: str | Path | None = None,
        cli_args: dict[str, Any] | None = None,
        *,
        camera_config: CameraConfig | None = None,
        use_threaded: bool | None = None,
        warmup_frames: int = 30,
        max_frames: int | None = None,
        rename_log: bool = True,
    ) -> InferResult:
        start = datetime.now()
        output_dir = Path("unknown")

        try:
            config, merger = build_infer_config(
                yaml_path=yaml_path,
                cli_args=cli_args,
            )

            logger.info("=" * 60)
            logger.info("开始 YOLO 推理 (task=%s)".center(60), config.task)
            logger.info("=" * 60)

            raw_model = config.model
            raw_source = config.source

            if not raw_model:
                raise ValueError(
                    "推理必须指定模型 (config.model)。例如：\n"
                    "  odp-predict --model train3-...-best.pt\n"
                    "或在 infer.yaml 里写 model: ..."
                )
            if not raw_source:
                raise ValueError(
                    "推理必须指定输入源 (config.source)。例如：\n"
                    "  odp-predict --source 0\n"
                    "  odp-predict --source image.jpg\n"
                    "  odp-predict --source ./images/\n"
                    "（若 infer.yaml 尚未生成，先跑: odp-gen-config infer）"
                )

            source = str(raw_source)
            logger.info("任务类型:    %s", config.task)
            logger.info("输入源(声明): %s", source)
            logger.info("模型(声明):  %s", raw_model)
            model_path = resolve_model_path(
                raw_model,
                search_dirs=[CHECKPOINTS_DIR, PRETRAINED_MODELS_DIR],
            )
            logger.info("模型(解析):  %s", model_path)

            log_effective_config(config, merger, logger=logger)
            log_override_chains(config, merger, logger=logger)

            project = config.project or str(RUNS_DIR / f"{config.task}_predict")
            output_dir = Path(project)
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info("输出目录(project): %s", output_dir)

            yolo_kwargs = config.to_ultralytics_kwargs()
            for key in _FRAMEWORK_PREDICT_KEYS:
                yolo_kwargs.pop(key, None)
            yolo_kwargs.setdefault("project", str(output_dir.parent))
            yolo_kwargs.setdefault("name", output_dir.name)

            model = YOLO(str(model_path))
            vid_stride = max(1, int(config.vid_stride or 1))

            frame_source = _create_frame_source(
                source,
                camera_config=camera_config,
                use_threaded=use_threaded,
                warmup_frames=warmup_frames,
            )

            logger.info("=" * 60)
            logger.info("启动推理 (frame_source)".center(60))
            logger.info("=" * 60)

            processed = 0
            seen = 0
            window = "odp-predict"

            with frame_source as src:
                for frame in src:
                    seen += 1
                    if vid_stride > 1 and (seen - 1) % vid_stride != 0:
                        continue

                    results = model.predict(frame.image, **yolo_kwargs)
                    r0 = results[0]
                    annotated = r0.plot(
                        line_width=config.line_width,
                        labels=config.show_labels,
                        conf=config.show_conf,
                        boxes=config.show_boxes,
                    )

                    stem = frame.info.filename or f"frame_{frame.info.frame_index:06d}"
                    if config.save:
                        out_name = Path(stem).stem + ".jpg"
                        out_path = output_dir / out_name
                        cv2.imwrite(str(out_path), annotated)

                    if config.save_txt:
                        labels_dir = output_dir / "labels"
                        labels_dir.mkdir(parents=True, exist_ok=True)
                        r0.save_txt(str(labels_dir / f"{Path(stem).stem}.txt"))

                    if config.show:
                        cv2.imshow(window, annotated)
                        key = cv2.waitKey(1) & 0xFF
                        if key in (ord("q"), 27):
                            logger.info("用户按键退出推理循环")
                            break

                    processed += 1
                    if max_frames and processed >= max_frames:
                        break

            if config.show:
                cv2.destroyAllWindows()

            audit_path = output_dir / "odp_audit.json"
            log_path = _find_project_log_path()
            infer_time = (datetime.now() - start).total_seconds()
            try:
                audit_payload = {
                    "kind": "predict",
                    "config": config.to_audit_snapshot(),
                    "merger": merger.to_audit_log(),
                    "result_summary": {
                        "source": source,
                        "frames_processed": processed,
                        "infer_time_sec": infer_time,
                        "log_path": str(log_path) if log_path else None,
                    },
                }
                audit_path.write_text(
                    json.dumps(audit_payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                logger.info("审计快照: %s", audit_path)
            except OSError as e:
                logger.warning("写审计快照失败(不影响推理结果): %s", e)
                audit_path = None

            if rename_log:
                rename_log_to_save_dir(output_dir, Path(raw_model).stem)

            logger.info("=" * 60)
            logger.info("推理总耗时: %.2f 秒", infer_time)
            logger.info("处理帧数:   %d", processed)
            logger.info("输出目录:   %s", output_dir)
            if log_path:
                logger.info("本次日志:   %s", log_path)
            logger.info("=" * 60)

            return InferResult(
                success=True,
                output_dir=output_dir,
                frames_processed=processed,
                infer_time=infer_time,
                audit_path=audit_path,
                log_path=log_path,
            )

        except Exception as e:
            logger.error("推理失败: %s", e, exc_info=True)
            infer_time = (datetime.now() - start).total_seconds()
            return InferResult(
                success=False,
                output_dir=output_dir,
                frames_processed=0,
                infer_time=infer_time,
                error=str(e),
                log_path=_find_project_log_path(),
            )


def predict_yolo(
    yaml_path: str | Path | None = None,
    cli_args: dict[str, Any] | None = None,
    **kwargs: Any,
) -> InferResult:
    return InferService().predict(
        yaml_path=yaml_path,
        cli_args=cli_args,
        **kwargs,
    )
