# 数据目录（不纳入 Git）

本目录下的数据集、训练产物和模型权重体积较大，**已从 Git 跟踪中排除**。
请在本机自行放置数据，或通过网盘 / 数据集官网下载。

## 推荐目录结构

```
data/
├── raw/<dataset>/          # 原始数据 (如 RSOD 的 Annotations + JPEGImages)
├── processed/<dataset>/    # odp-transform 输出 (包含 <dataset>.yaml 训练配置)
```

## 获取 RSOD 示例数据

1. 下载 RSOD 数据集到 `data/raw/rsod/`
2. 运行: `odp-transform --dataset rsod --format pascal_voc`
3. 训练配置: `data/processed/rsod.yaml` (由 odp-transform 自动生成)

## 其他路径（同样在 .gitignore 中）

- `models/` — 预训练权重与 checkpoints
- `runs/` — 训练运行输出
- `apps/platform/logs/` — platform 运行日志
- `apps/platform/.odp-meta/` — 元工具审计日志（如 odp-reset）
