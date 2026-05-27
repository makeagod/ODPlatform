# ODPlatform

通用目标检测开发平台 (Monorepo)。

**完整目录说明** → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 目录结构（精简）

```
ODPlatform/
├── apps/platform/          # 核心引擎 odp_platform（common / training / …）
├── configs/                # 共享配置：runtime/ + datasets/
├── data/                   # raw / processed / temp
├── docs/                   # ARCHITECTURE + ADR + 课程讲义
├── models/                 # pretrained / checkpoints
├── runs/                   # 训练 / 验证 / D4 报告
├── scripts/                # setup、数据集脚本
├── tests/                  # 工作区级集成测试
└── apps/platform/tests/    # 平台子系统单元测试
```

## 子系统与命令（按课程日）

| 日 | 模块 | 命令 |
|----|------|------|
| D3 | `data_pipeline` | `odp-transform` |
| D4 | `data_validation` | `odp-validate` |
| D5 | `runtime_config` | `odp-gen-config train` |
| D6 | `training` | `odp-train` |
| D7 | `evaluation` | `odp-val` |
| D8 | `inference` + `frame_source` | `odp-predict` |

## 开发环境

```bash
pip install -r requirements-dev.txt
# 或
bash scripts/setup-dev.sh
.\scripts\setup-dev.ps1
```

刷新 CLI entry-points：

```bash
pip install -e ./apps/platform --force-reinstall --no-deps
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `odp-init` | 创建项目目录结构 |
| `odp-reset` | 预览可清理目录 |
| `odp-gen-config train` | 生成 `configs/runtime/train.yaml` |
| `odp-train` | 训练（默认读根目录 runtime 配置） |

## 测试

```bash
pytest    # 含 tests/ 与 apps/platform/tests/
```
