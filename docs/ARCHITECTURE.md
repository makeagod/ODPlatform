# ODPlatform 目录架构

本文档对照课程压缩包 `odp_platform.zip`（含 `common/` + `training/`）与当前 Monorepo 终态，说明**每一层放什么、谁产出、谁消费**。

## 一、Monorepo 总览

```
ODPlatform/                          # 工作区根（.odp-workspace 标记）
│
├── apps/                            # 各端应用（可独立安装/部署）
│   ├── platform/                    # ★ 核心引擎：Python 包 odp_platform
│   ├── web-frontend/                # 预留：Web UI
│   ├── web-backend/                 # 预留：API 服务
│   └── desktop/                     # 预留：桌面端
│
├── configs/                         # ★ 共享配置（进 Git，可复现实验）
│   ├── runtime/                     # D5 运行配置 train / val / infer
│   └── datasets/                    # 可选：手写数据集契约（默认可用 data/processed/）
│
├── data/                            # 数据集资产（大文件不进 Git）
│   ├── raw/                         # D3 原始数据
│   ├── processed/                   # D3 产出：YOLO 布局 + *.yaml
│   └── temp/                        # 转换临时目录
│
├── models/                          # 模型资产（不进 Git）
│   ├── pretrained/                  # 官方 / 课程权重
│   └── checkpoints/                 # D6 归档 best / last
│
├── runs/                            # 运行产物（不进 Git）
│   ├── detect_train/                # ultralytics 训练
│   ├── detect_val/                  # ultralytics 验证
│   └── data_validation/             # D4 校验报告
│
├── docs/                            # 设计文档（ADR + 课程讲义）
├── scripts/                         # 工作区脚本（setup、数据集准备）
├── tests/                           # 工作区级集成测试
└── packages/                        # 跨端共享包（如 shared-schemas）
```

**原则**：共享资产放仓库根（`configs/`、`data/`、`models/`、`runs/`）；端私有资产放 `apps/platform/`（源码、`logs/`、`.odp-meta/`）。

---

## 二、课程 zip → `odp_platform` 包内分层

压缩包是 **D2 common + D6 training** 片段；完整平台按实训日扩展如下：

| 课程 | 目录 / 模块 | 职责 | CLI（若有） |
|------|-------------|------|-------------|
| D2 | `common/` | 路径、常量、跨任务工具（model/dataset 解析、指标、日志兼容层） | — |
| D2 | `logging/` | 日志装配（`setup_cli_logging`） | — |
| D3 | `data_pipeline/` | 格式转换、划分、产出 `data/processed/*.yaml` | `odp-transform` |
| D4 | `data_validation/` | 数据集健康度校验 | `odp-validate` |
| D5 | `runtime_config/` | 运行配置加载/合并/模板（只描述不执行） | `odp-gen-config` |
| D6 | `training/` | 训练编排（zip 内已有 `service.py` / `archive.py`） | `odp-train` |
| D7 | `evaluation/` | 验证编排 | `odp-val` |
| D8 铺垫 | `frame_source/` | 统一出帧（摄像头/视频/图/目录），**零依赖** `odp_platform` 其它子系统 | （库） |
| D8 | `inference/` | 推理编排 + `InferService` + `frame_source` | `odp-predict` |
| — | `cli/` | 各 `odp-*` 命令入口（装 handler + 调 service） | 见上 |

```
apps/platform/src/odp_platform/
├── common/              ← zip: common/（config_log, paths, result, model_path…）
├── logging/
├── data_pipeline/
├── data_validation/
├── runtime_config/
├── training/            ← zip: training/（service, archive）
├── evaluation/
├── cli/
└── _version.py
```

zip 中 **不应出现** 的内容（属构建产物，勿提交）：`__pycache__/`、`.pyc`。

---

## 三、配置与数据：两个 YAML 世界

| 目录 | 描述对象 | 典型字段 | 产出命令 |
|------|----------|----------|----------|
| `configs/runtime/` | **怎么跑** | epochs, batch, lr0, device | `odp-gen-config train` |
| `data/processed/*.yaml` | **数据长什么样** | path, train, val, nc, names | `odp-transform` |

不要混在同一目录——目录名即文档。

---

## 四、`apps/platform/` 端内布局

```
apps/platform/
├── src/odp_platform/    # 可安装 Python 包（pip install -e .）
├── tests/               # 平台单元 / 子系统测试
├── logs/                # 运行日志（按阶段分子目录 train/val/…）
├── docs/                # → 已迁移至仓库根 docs/platform/（见该目录 README）
├── pyproject.toml       # 包元数据 + odp-* entry-points
└── README.md
```

**不再使用** `apps/platform/configs/` 存放运行配置——统一使用仓库根 `configs/runtime/`。

---

## 五、测试放置规则

| 位置 | 内容 |
|------|------|
| `apps/platform/tests/` | `runtime_config`、`training`、`evaluation`、`logging` 等子系统测试 |
| `tests/` | 跨模块集成（如 `data_validation` e2e、`data_pipeline`） |

根目录 `pyproject.toml` 的 `testpaths` 同时包含上述两处。

---

## 六、常用路径速查（`paths.py` SSoT）

| 变量 | 路径 |
|------|------|
| `ROOT_DIR` | 含 `.odp-workspace` 的仓库根 |
| `APP_DIR` | `apps/platform` |
| `RUNTIME_CONFIGS_DIR` | `configs/runtime` |
| `DATASET_CONFIGS_DIR` | `data/processed`（Ultralytics 数据集 yaml） |
| `CONFIGS_DATASETS_DIR` | `configs/datasets`（可选手写 yaml） |
| `PRETRAINED_MODELS_DIR` | `models/pretrained` |
| `CHECKPOINTS_DIR` | `models/checkpoints` |
| `LOGGING_DIR` | `apps/platform/logs` |
| `RUNS_DIR` | `runs` |

---

## 七、与 zip 对齐的检查清单

- [x] `common/`、`training/` 在 `src/odp_platform/` 下，非仓库根
- [x] 权重在 `models/pretrained/`，不在仓库根散落 `*.pt`
- [x] 运行配置在 `configs/runtime/`，单一 SSoT
- [x] 训练 / 验证日志在 `apps/platform/logs/<阶段>/`
- [x] `frame_source/` 已集成（见 [D8-frame_source-铺垫.md](platform/D8-frame_source-铺垫.md)）
- [x] `inference/` + `odp-predict`（`infer_build` + `YOLOInferConfig`）
