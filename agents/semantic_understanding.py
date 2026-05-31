from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from contracts.base import validate_contract
from contracts.semantic import SemanticUnderstanding
from core.model_config import (
    DEFAULT_LLM_MAX_RETRIES,
    DEFAULT_LLM_TIMEOUT_SECONDS,
    DEFAULT_MODEL,
    model_for_role,
    resolve_llm_max_retries,
    resolve_llm_timeout,
)


def resolve_openai_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("VITE_OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OpenAI API key not found. Set OPENAI_API_KEY in .env. "
            "VITE_OPENAI_API_KEY is also supported as a local fallback."
        )
    return api_key


def compact_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def build_semantic_understanding_chain(model: str | None = None):
    api_key = resolve_openai_api_key()
    llm = ChatOpenAI(
        model=model_for_role("semantic", model),
        api_key=api_key,
        temperature=0,
        timeout=resolve_llm_timeout(),
        max_retries=resolve_llm_max_retries(),
    )
    structured_llm = llm.with_structured_output(SemanticUnderstanding)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a careful data analyst. Infer semantic meaning only from "
                "the provided dataset metadata, optional dataset description, and "
                "sample dataframe rows. Do not invent facts that are unsupported. "
                "Prefer concise, business-readable labels.",
            ),
            (
                "human",
                "Dataset metadata:\n{metadata_json}\n\n"
                "Dataframe head:\n{df_head}\n\n"
                "Return the semantic understanding for this dataset.",
            ),
        ]
    )

    return prompt | structured_llm


def generate_semantic_understanding(
    metadata: dict[str, Any],
    df_head: str,
    model: str | None = None,
) -> SemanticUnderstanding:
    chain = build_semantic_understanding_chain(model=model)
    result = chain.invoke(
        {
            "metadata_json": compact_json(metadata),
            "df_head": df_head,
        }
    )
    return validate_contract(SemanticUnderstanding, result)


def load_metadata(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dataframe_head_markdown(csv_path: Path, rows: int = 5) -> str:
    df = pd.read_csv(csv_path)
    return df.head(rows).to_markdown(index=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate semantic understanding from dataset metadata and CSV head."
    )
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    metadata = load_metadata(args.metadata)
    df_head = dataframe_head_markdown(args.csv, rows=args.rows)
    result = generate_semantic_understanding(
        metadata=metadata,
        df_head=df_head,
        model=args.model,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
