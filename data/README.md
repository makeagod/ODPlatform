# 数据目录（不纳入 Git）

本目录下的数据集、训练产物和模型权重体积较大，**已从 Git 跟踪中排除**。
请在本机自行放置数据，或通过网盘 / 数据集官网下载。

## 推荐目录结构

```
data/
├── raw/<dataset>/          # 原始数据 (如 RSOD 的 Annotations + JPEGImages)
├── processed/<dataset>/    # odp-transform 输出 (包含 <dataset>.yaml 训练配置)
```

数据集 yaml 的查找顺序见 [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)（`data/processed/` → `configs/datasets/`）。

## 获取 RSOD 示例数据

1. 下载 RSOD 数据集到 `data/raw/rsod/`
2. 运行: `odp-transform --dataset rsod --format pascal_voc`
3. 训练配置: `data/processed/rsod.yaml` (由 odp-transform 自动生成)

## VOC2028（PASCAL VOC，已接入示例）

原始数据在 `D:\VOC2028` 时，可用目录联接（不占双倍磁盘）：

```powershell
# 在仓库根目录执行（仅需一次）
cmd /c mklink /J "data\raw\voc2028" "D:\VOC2028"

odp-transform --dataset voc2028 --format pascal_voc
odp-validate --dataset voc2028 --task detect
```

- 处理后：`data/processed/voc2028.yaml`
- 类别：`hat`, `person`, `dog`（3 类）
- 划分：train 6065 / val 758 / test 758

一键完成（解压→转换→质检）：

```powershell
.\scripts\setup_voc2028.ps1
```

训练：

```powershell
# 专用配置 configs/runtime/train_voc2028.yaml
odp-train --yaml configs/runtime/train_voc2028.yaml --epochs 3 --batch 8 --device cpu
odp-train --yaml configs/runtime/train_voc2028.yaml --device 0
```

## 其他路径（同样在 .gitignore 中）

- `models/` — 预训练权重与 checkpoints
- `runs/` — 训练运行输出
- `apps/platform/logs/` — platform 运行日志
- `apps/platform/.odp-meta/` — 元工具审计日志（如 odp-reset）
