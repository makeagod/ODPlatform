# 数据目录（不纳入 Git）

本目录下的数据集、训练产物和模型权重体积较大，**已从 Git 跟踪中排除**。
请在本机自行放置数据，或通过网盘 / 数据集官网下载。

## 推荐目录结构

```
data/
├── raw/<dataset>/          # 原始数据 (如 RSOD 的 Annotations + JPEGImages)
├── processed/<dataset>/    # odp-transform 输出 (自动生成)
├── train/ val/ test/       # 镜像到训练目录 (odp-transform 自动同步)
├── temp/                   # 转换临时文件
└── rsod.yaml               # 可选: 训练配置副本 (主配置在 apps/platform/configs/datasets/)
```

## 获取 RSOD 示例数据

1. 下载 RSOD 数据集到 `data/raw/rsod/`
2. 运行: `odp-transform --dataset rsod --format pascal_voc`
3. 训练配置: `apps/platform/configs/datasets/rsod.yaml`

## 其他路径（同样在 .gitignore 中）

- `models/` — 预训练权重与 checkpoints
- `runs/` — 训练运行输出
- `.odp-meta/` — 工具审计日志
