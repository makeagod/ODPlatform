# -*- coding: utf-8 -*-
from odp_platform.runtime_config.schemas.predict import PREDICT_SCHEMA
from odp_platform.runtime_config.schemas.train import TRAIN_SCHEMA
from odp_platform.runtime_config.schemas.val import VAL_SCHEMA

SCHEMAS = {
    "train": TRAIN_SCHEMA,
    "val": VAL_SCHEMA,
    "predict": PREDICT_SCHEMA,
    "infer": PREDICT_SCHEMA,  # 与 odp-gen-config infer / infer.yaml 对齐
}
