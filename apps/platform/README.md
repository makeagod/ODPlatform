# ODPlatform — platform 端

目标检测平台核心引擎（`odp_platform` 包）。

安装：`pip install -e .`（在 `apps/platform` 目录下执行）

## 日志

| 目录 | 用途 |
|------|------|
| `logs/<阶段>/` | CLI 与流水线运行日志（`odp-init`、`odp-transform` 等） |
| `.odp-meta/logs/` | 元工具审计（`odp-reset`），清理 `logs/` 时保留 |

代码入口：`from odp_platform.logging import setup_cli_logging`

## 训练 (D6)

讲义：[docs/platform/D6-training-子系统.md](../../docs/platform/D6-training-子系统.md)

```powershell
pip install -e .

# CPU 冒烟（3 epoch）
odp-train --epochs 3 --batch 8 --device cpu --model yolov8n.pt --data rsod.yaml

# GPU
odp-train --epochs 3 --batch 8 --device 0 --model yolov8n.pt --data rsod.yaml
```

| 命令 | 说明 |
|------|------|
| `odp-train` | 默认 `configs/runtime/train.yaml` |
| `odp-train --no-pre-validate` | 跳过 D4 校验（不推荐） |

权重放入 `models/pretrained/`（如 `yolov8n.pt`）；数据需先 `odp-transform` + `odp-validate`。

## 推理 (D8)

```powershell
odp-gen-config infer
odp-predict --model yolov8n.pt --source image.jpg --device cpu
odp-predict --model best.pt --source 0 --show --camera-fps 30
```

`InferService` 编排 D5 + `frame_source` + ultralytics。讲义见 `docs/platform/D8-frame_source-铺垫.md`，示例见 `scripts/examples/frame_source/`。
