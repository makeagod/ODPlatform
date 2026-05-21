# ADR-004: data_validation 质检子系统

## 状态
已通过 (Accepted)

## 上下文

D3 `data_pipeline` 将原始数据转为 Ultralytics 可训练的 YAML 与目录结构，但不保证图像/标签成对、标签行合法、或 train/val/test 无 stem 泄露。D5 训练前需要独立质检，输出可读日志、JSON 报告与 CI 可用退出码。

## 决策

1. **注册表 + 装饰器 + 自动发现**：`@check(name)` 登记到模块级 dict，`pkgutil.iter_modules` 扫描 `checks/`；与 D3 相反，调度为**聚合执行**，一次跑完全部 check。
2. **CheckResult 四字段 + 四级 severity**：`CheckSeverity` 为字符串常量类（非 Enum）；`passed` 为 `@property` 派生，禁止与 `severity` 双存。
3. **DatasetSnapshot 一次扫描**：`build_snapshot` best-effort，解析失败写入 `yaml_load_error`；`frozen=True` + 容器用 `Tuple` 防串改。
4. **异常唯一兜底**：仅 `run_all_checks` → `_safe_run_one` 捕获 `Exception`，包装为 ERROR 级结果，不阻断其他 check。
5. **数据 / 展示分离**：`ValidationReport.to_dict()` 供 JSON；`render_to_logger` 三段式人类可读输出。
6. **SRP 只检测不修复**：问题由 `data_pipeline` 重跑修复，本模块不写回磁盘。
7. **端到端函数**：`validate_dataset()` 而非 `DatasetValidator` 类；`@time_it` 仅挂在 `build_snapshot` / `run_all_checks`。

## 拒绝的方案

| 方案 | 原因 |
|------|------|
| 每个 check 自己扫盘 | 重复 IO，snapshot 统一扫描 |
| `DatasetValidator` 类 | 无第二组公共方法，状态已在 `ValidationReport` |
| `ReportSection` 中间层 | YAGNI，当前仅 logger renderer |
| 砍掉 INFO 级 | 与 syslog 语义不对齐；pair 少量缺失需 INFO |
| `@wraps` 包装 check | traceback 多帧，单测难直接调原函数 |
| 重复注册覆盖 | 手误应 fail-fast |

## 已知边界

- 无 SAMPLE 抽样模式；大库全量扫描。
- `PAIR_MISSING_*` 阈值未配置化。
- `render.py` 按 check 名 if/elif 扩展时再 refactor。
- 不检查类别 ID 与 yaml `nc` 的业务一致性（除 label 行内范围）。

## 后果

- **正面**：CI 可集成；4 check 独立可测；加 check 只增文件不改框架。
- **负面**：全量扫描大库耗时随图像数线性增长（框架层 `@time_it` 可观测）。
