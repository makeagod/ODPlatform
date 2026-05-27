# configs/datasets — 数据集契约（可选）

描述 **数据长什么样**：`path`、`train`、`val`、`nc`、`names`。

## 默认位置

`odp-transform` 产出的 Ultralytics yaml 在 **`data/processed/<name>.yaml`**（D3 标准输出）。  
多数场景**不必**在本目录重复一份。

## 何时放这里

- 手写数据集契约、不经过 `odp-transform`
- 希望与 `data/processed/` 物理分离、仅保留 yaml 引用

平台按以下顺序查找数据集 yaml：

1. `data/processed/`
2. `configs/datasets/`（本目录）
3. `apps/platform/configs/datasets/`（已废弃，兼容旧路径）

## 示例

```bash
odp-validate --dataset rsod --task detect
odp-train --data rsod.yaml
```

`rsod.yaml` 解析为 `data/processed/rsod.yaml`。
