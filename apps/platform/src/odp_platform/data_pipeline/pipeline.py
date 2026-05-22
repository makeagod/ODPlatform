# -*- coding: utf-8 -*-
"""DatasetPipeline — D3 端到端门面（供 odp-transform CLI 调用）。"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from odp_platform.data_pipeline.orchestrator import DataPipelineOrchestrator
from odp_platform.data_pipeline.registry import ConvertOptions


class DatasetPipeline:
    """把 CLI 参数映射到 DataPipelineOrchestrator 一次 run。"""

    def __init__(
        self,
        dataset_name: str,
        annotation_format: str,
        task: str = "detect",
        train_rate: float = 0.8,
        val_rate: float = 0.1,
        classes: Optional[List[str]] = None,
        coco_cls91to80: bool = False,
        random_state: int = 42,
    ) -> None:
        self.dataset_name = dataset_name
        self.annotation_format = annotation_format
        self.task = task
        self.train_rate = train_rate
        self.val_rate = val_rate
        self.classes = classes
        self.coco_cls91to80 = coco_cls91to80
        self.random_state = random_state

    def run(self) -> Path:
        test_rate = max(0.0, 1.0 - self.train_rate - self.val_rate)
        options = ConvertOptions(
            task=self.task,
            classes=self.classes,
            coco_cls91to80=self.coco_cls91to80,
            random_state=self.random_state,
        )
        orchestrator = DataPipelineOrchestrator(
            dataset_name=self.dataset_name,
            raw_format=self.annotation_format,
            options=options,
        )
        return orchestrator.run_pipeline(
            train_ratio=self.train_rate,
            val_ratio=self.val_rate,
            test_ratio=test_rate,
        )
