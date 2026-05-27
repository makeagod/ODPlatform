# ADR-005: 运行配置子系统

## 状态
已通过 (Accepted)

## 上下文

训练/验证/推理参数分散在 CLI、YAML、默认值三处，存在静默缺配置、非法值晚暴露、无法溯源等问题（SRS P1~P5）。

## 决策

1. **字段 SSoT**：`FieldSpec` + `TaskSchema` 在 `schemas/` 唯一定义元数据与默认值。
2. **分层合并**：`defaults < yaml < cli` 可配置优先级；`ProvenanceReport` 记录覆盖链。
3. **Fail-fast**：YAML 缺失抛 `ConfigFileNotFoundError` 并附 `odp-gen-config <name>` 命令；未知字段拒绝。
4. **模板由代码生成**：`generate_config_template` / `ConfigGenerator` 写注释化 YAML，覆盖需 `--overwrite`（或兼容入口 `--force`）且默认备份。
5. **一站式 API**：`build_train_config` / `build_val_config` / `build_predict_config`。
6. **Ultralytics 边界**：`to_ultralytics_kwargs()` 剔除 `internal_fields` 与空值。

## 拒绝的方案

- 人工维护 YAML 模板（与代码漂移）
- 缺配置时静默写默认模板并继续（P5）
- 无溯源的 dict 合并

## 后果

- 正面：AC 可测、可扩展新 task/字段而不改 merge/validate 核心。
- 负面：未覆盖 Ultralytics 全参数字典，按需增量添加 `FieldSpec`。
