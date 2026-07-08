"""LLM 客户端配置、阶段路由、兼容调用。

从 run_bindings.py 提取，保持原有逻辑不变。
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass
from typing import Any

# run_step1 and nq are patched at runtime by run_bindings.py
import run_step1  # noqa: F401
from pipeline import run_pipeline as nq  # noqa: F401


# ========================================================================
# 默认配置 (从 run_bindings.py 常量区移入)
# ========================================================================

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_REASONING_EFFORT = "high"
DEFAULT_STAGE_MODELS = {
    "default": "deepseek-v4-pro",
    "adjudicator": "deepseek-v4-pro",
    "reviewer": "deepseek-v4-flash",
    "disagreement_reviewer": "deepseek-v4-pro",
    "plan_b": "deepseek-v4-flash",
}
DEFAULT_STAGE_REASONING = {
    "default": "off",
    "adjudicator": "high",
    "reviewer": "high",
    "disagreement_reviewer": "high",
    "plan_b": "high",
}

JSON_SYSTEM_PROMPT = (
    "You are a strict JSON generation engine for an exam evidence pipeline. "
    "Return only the requested JSON object. Do not add markdown, explanations, greetings, or commentary."
)

# ========================================================================
# 类型定义
# ========================================================================


@dataclass(frozen=True)
class LLMStageConfig:
    stage: str
    model: str
    reasoning_effort: str
    extra_body: dict[str, Any]


# ========================================================================
# 阶段配置路由
# ========================================================================


def _env_stage_name(stage: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "_", stage).strip("_").upper() or "DEFAULT"


def reasoning_extra_body(reasoning_effort: str, model: str) -> dict[str, Any]:
    value = str(reasoning_effort or "").strip().lower()
    if value in {"0", "false", "off", "none", "disabled", "disable", "no"}:
        return {"thinking": {"type": "disabled"}}
    if value:
        return {"thinking": {"type": "enabled"}, "reasoning_effort": value}
    if model.lower().startswith("deepseek"):
        return {"thinking": {"type": "disabled"}}
    return {}


def llm_stage_config(stage: str) -> LLMStageConfig:
    stage_key = _env_stage_name(stage)
    defaults_key = stage if stage in DEFAULT_STAGE_MODELS else "default"
    stage_model = os.environ.get(f"DS_{stage_key}_MODEL") or os.environ.get(f"{stage_key}_MODEL")
    stage_reasoning = (
        os.environ.get(f"DS_{stage_key}_REASONING_EFFORT")
        or os.environ.get(f"{stage_key}_REASONING_EFFORT")
    )
    model = (
        stage_model
        or os.environ.get("DS_MODEL")
        or DEFAULT_STAGE_MODELS.get(defaults_key)
        or DEFAULT_STAGE_MODELS.get(defaults_key, DEFAULT_MODEL)
    )
    reasoning_effort = (
        stage_reasoning
        or os.environ.get("DS_REASONING_EFFORT")
        or os.environ.get("REASONING_EFFORT")
        or DEFAULT_STAGE_REASONING.get(defaults_key)
        or DEFAULT_STAGE_REASONING.get(defaults_key, DEFAULT_REASONING_EFFORT)
    )
    extra_body = reasoning_extra_body(reasoning_effort, model)
    return LLMStageConfig(
        stage=stage,
        model=model,
        reasoning_effort=str(reasoning_effort or ""),
        extra_body=extra_body,
    )


def llm_stage_summary() -> dict[str, dict[str, Any]]:
    stages = ["adjudicator", "reviewer", "disagreement_reviewer"]
    return {
        stage: {
            "model": (cfg := llm_stage_config(stage)).model,
            "reasoning_effort": cfg.reasoning_effort,
            "extra_body": cfg.extra_body,
        }
        for stage in stages
    }


def parse_stage_model_requirements(values: list[str]) -> dict[str, str]:
    required: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"invalid stage model requirement {value!r}; expected stage=model")
        stage, model = value.split("=", 1)
        stage = stage.strip()
        model = model.strip()
        if not stage or not model:
            raise ValueError(f"invalid stage model requirement {value!r}; expected stage=model")
        required[stage] = model
    return required


def assert_stage_model_requirements(
    model_plan: dict[str, dict[str, Any]], required: dict[str, str]
) -> None:
    mismatches: list[str] = []
    for stage, expected in required.items():
        actual = str(model_plan.get(stage, {}).get("model", ""))
        if actual != expected:
            mismatches.append(f"{stage}: expected {expected}, actual {actual or '<missing>'}")
    if mismatches:
        detail = "; ".join(mismatches)
        raise SystemExit(f"[reuse] model preflight failed: {detail}")


def print_model_plan(model_plan: dict[str, dict[str, Any]]) -> None:
    print("[reuse] effective model plan:")
    for stage in ("adjudicator", "reviewer", "disagreement_reviewer"):
        cfg = model_plan.get(stage, {})
        print(
            f"[reuse]   {stage}: model={cfg.get('model', '')} "
            f"reasoning_effort={cfg.get('reasoning_effort', '')} "
            f"extra_body={json.dumps(cfg.get('extra_body', {}), ensure_ascii=False)}"
        )


def configure_llm_from_env() -> None:
    """Apply default OpenAI-compatible settings after importing run_step1."""
    os.environ.setdefault("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL)
    cfg = llm_stage_config("default")
    run_step1.MODEL = cfg.model
    run_step1.V4_NO_THINK = cfg.extra_body


# ========================================================================
# LLM 调用
# ========================================================================

_ORIGINAL_RUN_STEP1_CALL_LLM = run_step1.call_llm
_ORIGINAL_NQ_CALL_LLM_TRACED = nq._call_llm_traced
_RETRIEVAL_LOCK = threading.Lock()
_THREAD_LOCAL = threading.local()


def _llm_messages(prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": JSON_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]


def call_llm_compat(
    client: Any,
    prompt: str,
    max_tokens: int,
    retries: int | None = None,
    stage: str = "default",
) -> str:
    """OpenAI-compatible LLM call with a JSON-only system guard."""
    attempt_retries = retries if retries is not None else run_step1.LLM_RETRY
    last_error: Exception | None = None
    cfg = llm_stage_config(stage)
    for attempt in range(attempt_retries):
        try:
            response = client.chat.completions.create(
                model=cfg.model,
                messages=_llm_messages(prompt),
                temperature=0,
                max_tokens=max_tokens,
                extra_body=cfg.extra_body,
            )
            content = (response.choices[0].message.content or "").strip()
            if not content:
                finish_reason = getattr(response.choices[0], "finish_reason", "")
                usage = getattr(response, "usage", None)
                completion_tokens = (
                    getattr(usage, "completion_tokens", None) if usage is not None else None
                )
                reasoning_content = (
                    getattr(response.choices[0].message, "reasoning_content", "") or ""
                )
                raise RuntimeError(
                    "LLM returned empty content"
                    f" finish_reason={finish_reason}"
                    f" completion_tokens={completion_tokens}"
                    f" reasoning_chars={len(reasoning_content)}"
                )
            return content
        except Exception as exc:
            last_error = exc
            if attempt < attempt_retries - 1:
                time.sleep(3 + attempt * 2)
    raise RuntimeError(str(last_error) if last_error else "LLM call failed")


def _patched_nq_call_llm_traced(
    client: Any,
    stage: str,
    prompt: str,
    max_tokens: int,
    retries: int | None = None,
) -> tuple[str, dict[str, Any]]:
    """Patched traced LLM call that records full trace including model config.

    blind_leakage_check is set to None here; run_bindings.py patches it after import.
    """
    started = time.perf_counter()
    attempt_retries = retries if retries is not None else run_step1.LLM_RETRY
    response_obj: Any = None
    last_error: Exception | None = None
    cfg = llm_stage_config(stage)
    for attempt in range(attempt_retries):
        try:
            kwargs: dict[str, Any] = {
                "model": cfg.model,
                "messages": _llm_messages(prompt),
                "temperature": 0,
                "max_tokens": max_tokens,
                "extra_body": cfg.extra_body,
            }
            response_obj = client.chat.completions.create(**kwargs)
            content = (response_obj.choices[0].message.content or "").strip()
            if not content:
                finish_reason = getattr(response_obj.choices[0], "finish_reason", "")
                usage = getattr(response_obj, "usage", None)
                completion_tokens = (
                    getattr(usage, "completion_tokens", None) if usage is not None else None
                )
                reasoning_content = (
                    getattr(response_obj.choices[0].message, "reasoning_content", "") or ""
                )
                raise RuntimeError(
                    "LLM returned empty content"
                    f" finish_reason={finish_reason}"
                    f" completion_tokens={completion_tokens}"
                    f" reasoning_chars={len(reasoning_content)}"
                )
            trace = nq._record_llm_trace(stage, max_tokens, started, response_obj, prompt, content)
            trace["model"] = cfg.model
            trace["reasoning_effort"] = cfg.reasoning_effort
            trace["extra_body"] = cfg.extra_body
            trace["blind_leakage_check"] = None  # patched by run_bindings after import
            return content, trace
        except Exception as exc:
            last_error = exc
            if attempt < attempt_retries - 1:
                time.sleep(3 + attempt * 2)
    trace = {
        "stage": stage,
        "model": cfg.model,
        "reasoning_effort": cfg.reasoning_effort,
        "extra_body": cfg.extra_body,
        "max_tokens": max_tokens,
        "status": "error",
        "error": str(last_error) if last_error else "LLM call failed",
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
    }
    raise RuntimeError(trace["error"])


# Apply patches at import time
run_step1.call_llm = call_llm_compat
nq._call_llm_traced = _patched_nq_call_llm_traced
