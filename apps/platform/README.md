# ODPlatform — platform 端

目标检测平台核心引擎（`odp_platform` 包）。

安装：`pip install -e .`（在 `apps/platform` 目录下执行）

## 日志

| 目录 | 用途 |
|------|------|
| `logs/<阶段>/` | CLI 与流水线运行日志（`odp-init`、`odp-transform` 等） |
| `.odp-meta/logs/` | 元工具审计（`odp-reset`），清理 `logs/` 时保留 |

代码入口：`from odp_platform.logging import setup_cli_logging`
