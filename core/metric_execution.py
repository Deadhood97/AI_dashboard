from __future__ import annotations

import ast
import logging
import textwrap
from typing import Any

import numpy as np
import pandas as pd

from agents.metric_code_planner import generate_metric_code_plan, repair_metric_code_plan
from contracts.base import validate_contract
from contracts import PandasMetricPlan, SemanticUnderstanding

from .artifacts import save_failed_metric_plan


logger = logging.getLogger(__name__)


def sanitize_generated_code(code: str) -> str:
    allowed_imports = {"import pandas as pd", "import numpy as np"}
    cleaned_code = textwrap.dedent(code).strip()
    if cleaned_code.startswith("```"):
        cleaned_lines = cleaned_code.splitlines()
        if cleaned_lines and cleaned_lines[0].strip().startswith("```"):
            cleaned_lines = cleaned_lines[1:]
        if cleaned_lines and cleaned_lines[-1].strip() == "```":
            cleaned_lines = cleaned_lines[:-1]
        cleaned_code = "\n".join(cleaned_lines)
    cleaned_code = textwrap.dedent(cleaned_code).strip()

    lines = []
    for line in cleaned_code.splitlines():
        if line.strip() in allowed_imports:
            continue
        lines.append(line)
    cleaned_code = "\n".join(lines)

    try:
        ast.parse(cleaned_code)
    except IndentationError:
        normalized_lines: list[str] = []
        previous_significant = ""
        for line in cleaned_code.splitlines():
            if line.startswith((" ", "\t")) and not previous_significant.endswith(":"):
                normalized_lines.append(line.lstrip())
            else:
                normalized_lines.append(line)
            if line.strip():
                previous_significant = line.rstrip()
        cleaned_code = "\n".join(normalized_lines)
    except SyntaxError:
        return cleaned_code

    return cleaned_code


def validate_generated_code(code: str) -> None:
    tree = ast.parse(code)
    blocked_names = {"open", "exec", "eval", "compile", "__import__", "input"}
    blocked_roots = {
        "os",
        "sys",
        "subprocess",
        "socket",
        "requests",
        "pathlib",
        "shutil",
        "scipy",
        "sklearn",
        "statsmodels",
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("Generated code may not import modules.")
        if isinstance(node, ast.While):
            raise ValueError("Generated code may not use while loops.")
        if isinstance(node, ast.Name) and node.id in {"__builtins__", "__loader__", "__spec__"}:
            raise ValueError("Generated code may not access interpreter internals.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in blocked_names:
                raise ValueError(f"Generated code may not call {node.func.id}.")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                raise ValueError("Generated code may not access dunder attributes.")
            root = node
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name) and root.id in blocked_roots:
                raise ValueError(f"Generated code may not access {root.id}.")


def execute_metric_plan(df: pd.DataFrame, metric_plan: PandasMetricPlan) -> dict[str, Any]:
    metric_plan = validate_contract(PandasMetricPlan, metric_plan)
    code = sanitize_generated_code(metric_plan.pandas_code)
    validate_generated_code(code)
    safe_builtins = {
        "ValueError": ValueError,
        "TypeError": TypeError,
        "Exception": Exception,
        "len": len,
        "range": range,
        "sorted": sorted,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "enumerate": enumerate,
        "isinstance": isinstance,
        "zip": zip,
        "all": all,
        "any": any,
    }
    globals_dict = {"__builtins__": safe_builtins, "pd": pd, "np": np}
    locals_dict: dict[str, Any] = {"df": df.copy()}
    exec(compile(code, "<metric_plan>", "exec"), globals_dict, locals_dict)
    analysis_outputs = locals_dict.get("analysis_outputs")
    if not isinstance(analysis_outputs, dict):
        raise ValueError("Metric plan code must create analysis_outputs as a dictionary.")
    return analysis_outputs


def generate_executable_metric_plan(
    df: pd.DataFrame,
    semantic_understanding: SemanticUnderstanding,
    df_head: str,
    metadata: dict[str, Any] | None = None,
    max_repairs: int = 2,
) -> tuple[PandasMetricPlan, dict[str, Any]]:
    semantic_understanding = validate_contract(SemanticUnderstanding, semantic_understanding)
    metric_plan = generate_metric_code_plan(
        semantic_understanding=semantic_understanding,
        df_head=df_head,
    )
    metric_plan = validate_contract(PandasMetricPlan, metric_plan)
    for attempt in range(max_repairs + 1):
        try:
            return metric_plan, execute_metric_plan(df, metric_plan)
        except Exception as exc:
            sanitized_code = sanitize_generated_code(metric_plan.pandas_code)
            error_message = f"{type(exc).__name__}: {exc}"
            if metadata is not None:
                failed_path = save_failed_metric_plan(
                    metadata,
                    metric_plan,
                    error_message,
                    sanitized_code,
                )
                logger.info("Saved failed metric plan attempt: %s", failed_path)
            if attempt >= max_repairs:
                raise
            logger.info("Repairing metric plan after execution failure: %s", exc)
            metric_plan = repair_metric_code_plan(
                failed_plan=metric_plan,
                semantic_understanding=semantic_understanding,
                df_head=df_head,
                error_message=error_message,
                failing_code=sanitized_code,
            )
            metric_plan = validate_contract(PandasMetricPlan, metric_plan)

    raise RuntimeError("Metric plan repair loop exited unexpectedly.")
