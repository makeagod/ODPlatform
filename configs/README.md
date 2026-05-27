# configs — 共享配置（进 Git）

本目录存放**可复现实验**的配置文件，与 `data/`、`models/` 同级，全工作区共享。

## 子目录

| 目录 | 含义 | 生成方式 |
|------|------|----------|
| [`runtime/`](runtime/README.md) | 训练 / 验证 / 推理**跑法**（D5） | `odp-gen-config train` |
| [`datasets/`](datasets/README.md) | 可选：手写数据集契约 | 通常用 `data/processed/` 即可 |

**不要**把 ultralytics 训练参数写进 `data/processed/*.yaml`，也不要把 `path/train/val` 写进 `runtime/*.yaml`。
