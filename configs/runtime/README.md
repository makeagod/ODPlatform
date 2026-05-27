# configs/runtime — 运行配置（D5）

描述 **怎么跑**：epochs、batch、device、优化器等。

## 生成模板

```bash
odp-gen-config train
odp-gen-config val
odp-gen-config infer    # 默认 configs/runtime/infer.yaml
```

## 使用

```bash
odp-train --yaml configs/runtime/train.yaml
odp-val  --model best.pt --data rsod.yaml
```

CLI 覆盖 YAML 中同名字段。优先级：**CLI > YAML > 代码默认值**。

## 文件说明

| 文件 | 用途 |
|------|------|
| `train.yaml` | 默认训练配置 |
| `val.yaml` | 默认验证配置 |
| `infer.yaml` | 默认推理配置 |
| `train_voc2028.yaml` | VOC2028 实验示例 |
| `*.bak.*` | `odp-gen-config --overwrite` 自动备份，可本地删除 |
