from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from contracts import PandasMetricPlan, SemanticUnderstanding
from core.artifacts import failed_metric_plan_path_for, slugify_filename
from core.dataset_metadata import build_dataframe_context, normalize_dataset_metadata
from core.metric_execution import generate_executable_metric_plan


BenchmarkRunner = Callable[..., tuple[PandasMetricPlan, dict[str, Any]]]
BENCHMARK_DIR = Path("artifacts") / "benchmarks" / "metric_models"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_semantic_understanding(path: Path) -> SemanticUnderstanding:
    return SemanticUnderstanding.model_validate_json(path.read_text(encoding="utf-8"))


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


def summarize_output_value(value: Any) -> dict[str, Any]:
    if isinstance(value, pd.DataFrame):
        return {
            "type": "DataFrame",
            "rows": int(len(value)),
            "columns": [str(column) for column in value.columns],
        }
    if isinstance(value, pd.Series):
        return {
            "type": "Series",
            "rows": int(len(value)),
            "name": str(value.name) if value.name is not None else None,
        }
    if isinstance(value, dict):
        return {
            "type": "dict",
            "keys": [str(key) for key in value.keys()],
        }
    if isinstance(value, (list, tuple)):
        return {
            "type": type(value).__name__,
            "items": len(value),
        }
    return {
        "type": type(value).__name__,
        "value": json_safe(value),
    }


def summarize_outputs(outputs: dict[str, Any]) -> dict[str, Any]:
    return {key: summarize_output_value(value) for key, value in outputs.items()}


@contextmanager
def metric_model_environment(model: str, timeout_seconds: float | None) -> Iterator[None]:
    keys = [
        "OPENAI_METRIC_CODE_MODEL",
        "OPENAI_METRIC_REPAIR_MODEL",
        "OPENAI_TIMEOUT_SECONDS",
    ]
    previous = {key: os.environ.get(key) for key in keys}
    os.environ["OPENAI_METRIC_CODE_MODEL"] = model
    os.environ["OPENAI_METRIC_REPAIR_MODEL"] = model
    if timeout_seconds is not None:
        os.environ["OPENAI_TIMEOUT_SECONDS"] = str(timeout_seconds)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def benchmark_metadata_for_model(metadata: dict[str, Any], model: str) -> dict[str, Any]:
    benchmark_metadata = normalize_dataset_metadata(metadata)
    source_file = str(benchmark_metadata.get("source_file", "dataset.csv"))
    stem = Path(source_file).stem
    suffix = Path(source_file).suffix or ".csv"
    benchmark_metadata["source_file"] = f"benchmark_{slugify_filename(model)}_{stem}{suffix}"
    return benchmark_metadata


def count_failed_attempts(metadata: dict[str, Any]) -> int:
    failed_path = failed_metric_plan_path_for(metadata)
    prefix = failed_path.name.split("_failed_metric_plan_", 1)[0]
    return len(list(failed_path.parent.glob(f"{prefix}_failed_metric_plan_*.json")))


def run_single_model_benchmark(
    *,
    model: str,
    df: pd.DataFrame,
    metadata: dict[str, Any],
    semantic_understanding: SemanticUnderstanding,
    df_context: str,
    max_repairs: int,
    timeout_seconds: float | None,
    runner: BenchmarkRunner = generate_executable_metric_plan,
) -> dict[str, Any]:
    benchmark_metadata = benchmark_metadata_for_model(metadata, model)
    failed_before = count_failed_attempts(benchmark_metadata)
    started = datetime.now(timezone.utc).isoformat()
    start_time = time.perf_counter()
    result: dict[str, Any] = {
        "model": model,
        "status": "running",
        "started_at": started,
        "max_repairs": max_repairs,
        "timeout_seconds": timeout_seconds,
    }

    with metric_model_environment(model, timeout_seconds):
        try:
            metric_plan, outputs = runner(
                df=df,
                semantic_understanding=semantic_understanding,
                df_head=df_context,
                metadata=benchmark_metadata,
                max_repairs=max_repairs,
            )
        except Exception as exc:
            result.update(
                {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(limit=8),
                }
            )
        else:
            result.update(
                {
                    "status": "succeeded",
                    "declared_output_count": len(metric_plan.analysis_outputs),
                    "produced_output_count": len(outputs),
                    "declared_output_keys": [output.key for output in metric_plan.analysis_outputs],
                    "produced_output_keys": list(outputs.keys()),
                    "output_summaries": summarize_outputs(outputs),
                }
            )

    failed_after = count_failed_attempts(benchmark_metadata)
    duration_seconds = time.perf_counter() - start_time
    result.update(
        {
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration_seconds, 3),
            "failed_attempt_count": failed_after - failed_before,
        }
    )
    return result


def write_report(report: dict[str, Any], output_dir: Path = BENCHMARK_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    path = output_dir / f"{timestamp}_metric_model_benchmark.json"
    path.write_text(json.dumps(report, indent=2, default=json_safe), encoding="utf-8")
    return path


def print_console_table(results: list[dict[str, Any]]) -> None:
    print("model,status,seconds,failed_attempts,declared_outputs,produced_outputs,error")
    for result in results:
        print(
            ",".join(
                [
                    str(result.get("model", "")),
                    str(result.get("status", "")),
                    str(result.get("duration_seconds", "")),
                    str(result.get("failed_attempt_count", "")),
                    str(result.get("declared_output_count", 0)),
                    str(result.get("produced_output_count", 0)),
                    str(result.get("error_type", "")),
                ]
            )
        )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark metric planning/execution across OpenAI models.")
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--semantic", type=Path, required=True)
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--max-repairs", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=float, default=None)
    parser.add_argument("--output-dir", type=Path, default=BENCHMARK_DIR)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    metadata = normalize_dataset_metadata(read_json(args.metadata))
    df = pd.read_csv(args.csv)
    semantic_understanding = load_semantic_understanding(args.semantic)
    df_context = build_dataframe_context(metadata, df)

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "csv": str(args.csv),
        "metadata": str(args.metadata),
        "semantic": str(args.semantic),
        "models": args.models,
        "max_repairs": args.max_repairs,
        "timeout_seconds": args.timeout_seconds,
        "results": [],
    }

    for model in args.models:
        print(f"Running metric benchmark for {model}...", flush=True)
        report["results"].append(
            run_single_model_benchmark(
                model=model,
                df=df,
                metadata=metadata,
                semantic_understanding=semantic_understanding,
                df_context=df_context,
                max_repairs=args.max_repairs,
                timeout_seconds=args.timeout_seconds,
            )
        )
        print_console_table(report["results"])

    report_path = write_report(report, args.output_dir)
    print(f"Saved benchmark report: {report_path}")


if __name__ == "__main__":
    main()
