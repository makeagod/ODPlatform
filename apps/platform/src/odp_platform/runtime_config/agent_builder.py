# -*- coding: utf-8 -*-
"""智能体动态调参 (Agent-in-the-Loop)。

利用 LLM 根据自然语言意图自动生成符合 fields.py 规格的配置字典，
通过 validate.py 防御性校验，失败时支持轻量级 Self-Correction 循环。
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from odp_platform.runtime_config.exceptions import ConfigValidationError
from odp_platform.runtime_config.fields import get_all_field_specs
from odp_platform.runtime_config.provenance import ProvenanceReport
from odp_platform.runtime_config.schemas import SCHEMAS
from odp_platform.runtime_config.validate import validate_config

logger = logging.getLogger(__name__)

MAX_SELF_CORRECTION_ROUNDS = 2


# ── System Prompt ────────────────────────────────────────────────────────────


def _build_system_prompt(task: str) -> str:
    """构造注入全部字段规格的 System Prompt。"""
    all_specs = get_all_field_specs(task)
    task_specs = all_specs[task]

    lines = [
        "你是一个 YOLO 目标检测/分割模型的配置专家。",
        "根据用户的自然语言意图，生成符合规范的配置参数。",
        "",
        "## 可用字段规格",
        "",
    ]

    groups: dict[str, list[dict[str, Any]]] = {}
    for spec in task_specs:
        g = spec.get("group", "general")
        groups.setdefault(g, []).append(spec)

    for group_name, fields in groups.items():
        lines.append(f"### {group_name}")
        lines.append("")
        for f in fields:
            constraints: list[str] = []
            if "min_value" in f:
                constraints.append(f"≥{f['min_value']}")
            if "max_value" in f:
                constraints.append(f"≤{f['max_value']}")
            if "choices" in f:
                constraints.append(f"可选: {f['choices']}")

            constraint_str = f", 约束: {', '.join(constraints)}" if constraints else ""
            lines.append(
                f"- **{f['name']}** ({f['type']}, 默认: {f['default']!r}{constraint_str}): {f['description']}"
            )
            if f.get("examples"):
                lines.append(f"  示例: {f['examples']}")
            if f.get("tuning_tips"):
                for tip in f["tuning_tips"]:
                    lines.append(f"  [调参建议] {tip}")
        lines.append("")

    lines.extend([
        "## 输出规则",
        "",
        "1. 只输出一个 JSON 对象，不要包含任何解释、markdown 标记或代码块围栏",
        "2. JSON 的键是字段名，值是你推荐的值",
        "3. 只需包含你想要从默认值修改的字段；未提及的字段将使用默认值",
        "4. 严格遵守每个字段的类型和约束",
        "5. batch 字段不能设为 0（用 -1 表示自动选择批次大小）",
        "6. 根据用户意图智能调参：",
        '   - "低显存" → 减小 batch、imgsz，减少 workers',
        '   - "极速收敛" → 增大 lr0、减少 epochs、增大 mosaic',
        '   - "高精度" → 增大 imgsz、增大 epochs、降低 lr0',
        '   - "轻量快速" → 减小 imgsz、减少 epochs、减小 batch',
        "",
        "只输出 JSON：",
    ])

    return "\n".join(lines)


# ── LLM Client ───────────────────────────────────────────────────────────────


def _get_llm_client(base_url: str | None = None, api_key: str | None = None):
    """获取 OpenAI 兼容的 LLM 客户端（支持 OpenAI / Ollama / 任意兼容端点）。"""
    from openai import OpenAI

    effective_base_url = (
        base_url
        or os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("AGENT_BUILDER_BASE_URL")
    )
    effective_api_key = (
        api_key
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("AGENT_BUILDER_API_KEY", "ollama")
    )

    if not effective_base_url:
        raise RuntimeError(
            "未配置 LLM base_url。请设置环境变量 OPENAI_BASE_URL 或 "
            "AGENT_BUILDER_BASE_URL，或传入 base_url 参数。\n"
            "Ollama 示例: base_url='http://localhost:11434/v1'"
        )

    return OpenAI(base_url=effective_base_url, api_key=effective_api_key)


# ── JSON 提取 ────────────────────────────────────────────────────────────────


def _extract_json(text: str) -> str:
    """从 LLM 原始响应中鲁棒提取 JSON 字符串。"""
    text = text.strip()

    # 尝试匹配 ```json ... ``` 或 ``` ... ``` 代码块
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # 尝试找到最外层的 { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]

    raise ValueError(f"无法从 LLM 响应中提取 JSON，原始输出前 500 字符: {text[:500]}")


# ── 类型强制 ─────────────────────────────────────────────────────────────────


def _coerce_value(value: Any, target_type: type) -> Any:
    """尝试将 value 强制转为 target_type；失败时返回原值，交给 validate 报错。"""
    if isinstance(value, target_type):
        return value
    if target_type is bool:
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return value


# ── 校验 ─────────────────────────────────────────────────────────────────────


def _validate_config_dict(values: dict[str, Any], task: str) -> list[str]:
    """对配置 dict 执行防御性校验，返回错误列表（空列表表示通过）。"""
    schema = SCHEMAS[task]
    provenance = ProvenanceReport()

    # 记录 agent 设置的字段
    for key, val in values.items():
        provenance.record(key, "agent", val)
    # 记录默认值字段
    for key, default_val in schema.defaults_dict().items():
        if key not in values:
            provenance.record(key, "defaults", default_val)

    merged = dict(schema.defaults_dict())
    merged.update(values)

    try:
        validate_config(schema, merged, provenance)
        return []
    except ConfigValidationError as e:
        return [str(e)]


# ── 主入口 ───────────────────────────────────────────────────────────────────


def generate_config_by_agent(
    user_intent: str,
    task: str = "train",
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """根据自然语言意图，利用 LLM 自动生成配置字典。

    支持最多 2 轮 Self-Correction：若 validate_config 校验失败，
    会将错误信息反馈给 LLM 重新生成。

    Args:
        user_intent: 用户自然语言意图，如 ``"低显存极速收敛"``。
        task: 任务类型，可选 ``"train"`` / ``"val"`` / ``"predict"``。
        model: LLM 模型名。默认从 ``AGENT_BUILDER_MODEL`` 环境变量读取，
               最终回退到 ``"gpt-4o-mini"``。
        base_url: LLM API 地址。默认从 ``OPENAI_BASE_URL`` 或
                  ``AGENT_BUILDER_BASE_URL`` 读取。
        api_key: API 密钥。默认从 ``OPENAI_API_KEY`` 或
                 ``AGENT_BUILDER_API_KEY`` 读取。

    Returns:
        经过校验的完整配置字典（agent 值叠加于默认值之上）。

    Raises:
        RuntimeError: 自修复耗尽仍无法通过校验时抛出。
        RuntimeError: 未配置 LLM base_url 时抛出。
    """
    if task not in SCHEMAS:
        raise ValueError(f"未知任务类型: {task!r}，可选: {list(SCHEMAS.keys())}")

    effective_model = model or os.environ.get("AGENT_BUILDER_MODEL", "gpt-4o-mini")
    client = _get_llm_client(base_url=base_url, api_key=api_key)
    system_prompt = _build_system_prompt(task)
    schema = SCHEMAS[task]
    fmap = schema.field_map()

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"意图: {user_intent}\n任务类型: {task}"},
    ]

    last_errors: list[str] = []

    for round_idx in range(1 + MAX_SELF_CORRECTION_ROUNDS):
        logger.info("Agent 调参第 %d/%d 轮", round_idx + 1, 1 + MAX_SELF_CORRECTION_ROUNDS)

        response = client.chat.completions.create(
            model=effective_model,
            messages=messages,
            temperature=0.1,
        )
        raw = response.choices[0].message.content or ""

        # 解析 JSON
        try:
            json_str = _extract_json(raw)
            agent_values = json.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            last_errors = [f"JSON 解析失败: {e}"]
            if round_idx < MAX_SELF_CORRECTION_ROUNDS:
                messages.append({"role": "assistant", "content": raw})
                messages.append({
                    "role": "user",
                    "content": (
                        f"你的输出无法解析为 JSON。请只输出一个纯 JSON 对象。\n"
                        f"错误: {last_errors[0]}"
                    ),
                })
                continue
            break

        if not isinstance(agent_values, dict):
            last_errors = [f"LLM 输出不是 JSON 对象，而是 {type(agent_values).__name__}"]
            if round_idx < MAX_SELF_CORRECTION_ROUNDS:
                messages.append({"role": "assistant", "content": raw})
                messages.append({
                    "role": "user",
                    "content": "请输出一个 JSON 对象（{...}），不要输出数组或其他类型。",
                })
                continue
            break

        # 过滤未知字段 + 类型强制
        cleaned: dict[str, Any] = {}
        for key, val in agent_values.items():
            if key not in fmap:
                continue
            spec = fmap[key]
            cleaned[key] = _coerce_value(val, type(spec.default))
        agent_values = cleaned

        # 校验
        errors = _validate_config_dict(agent_values, task)
        if not errors:
            merged = dict(schema.defaults_dict())
            merged.update(agent_values)
            logger.info("Agent 配置生成成功（第 %d 轮）", round_idx + 1)
            return merged

        last_errors = errors
        logger.warning("校验失败（第 %d 轮）: %s", round_idx + 1, errors)

        if round_idx < MAX_SELF_CORRECTION_ROUNDS:
            messages.append({"role": "assistant", "content": raw})
            error_detail = "\n".join(errors)
            messages.append({
                "role": "user",
                "content": (
                    f"你上一次输出的配置校验失败，请根据以下错误修正：\n\n"
                    f"{error_detail}\n\n"
                    f"请重新输出修正后的 JSON 配置。只输出 JSON，不要解释。"
                ),
            })

    raise RuntimeError(
        f"自修复耗尽（{MAX_SELF_CORRECTION_ROUNDS} 轮），仍存在以下校验错误:\n"
        + "\n".join(last_errors)
    )
