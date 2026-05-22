# ODPlatform

通用目标检测开发平台 (Monorepo)。

## 目录结构

```
ODPlatform/
├── apps/platform/     # 核心引擎 (odp_platform)
├── configs/           # 手工配置
├── data/              # 数据集 (raw / processed)
├── docs/              # 设计文档 (ADR)
├── logs/              # 运行时日志
├── models/            # 模型权重
├── runs/              # 训练输出
├── scripts/           # 工作区脚本
├── tests/             # 测试
└── pyproject.toml     # 工作区工具配置 (ruff / pytest)
```

## 开发环境

```bash
# 首次安装 (含依赖 + 注册 odp-init / odp-reset)
pip install -r requirements-dev.txt

# 或
bash scripts/setup-dev.sh        # Git Bash / Linux
.\scripts\setup-dev.ps1          # PowerShell
```

新增或修改 `pyproject.toml` 里的 `[project.scripts]` 后，刷新 CLI：

```bash
pip install -e ./apps/platform --force-reinstall --no-deps
# 或
bash scripts/setup-dev.sh --reinstall-only
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `odp-init` | 创建项目所需目录结构 |
| `odp-reset` | 预览可清理目录 (默认 dry-run) |
| `odp-reset --yes` | 执行清理 (需输入 `RESET` 确认) |
| `python scripts/reset_project.py` | 同上 (无需 pip install) |

## D2.5 灾难现场 (测试 odp-reset)

生成约 5650 个测试文件,用于演练 reset 保护逻辑与删除性能:

```bash
bash scripts/make_disaster_data.sh      # Git Bash / Linux / macOS
.\scripts\make_disaster_data.ps1        # Windows PowerShell
```

然后:

```bash
odp-reset              # 预览: raw 与 pretrained 应受保护
odp-reset --yes        # 真正清理 (需输入 RESET)
```
