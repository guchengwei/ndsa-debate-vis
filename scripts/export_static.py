#!/usr/bin/env python3
"""Export the cached thesis example into browser-friendly JSON."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DEFAULT_OUTPUT = ROOT / "docs" / "data.json"
DEFAULT_CLAIM = "~a>~d"


def load_knowledge_base() -> tuple[str, dict[str, str], dict[str, str]]:
    with (DATA_DIR / "debate_kb.csv").open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        title = next(reader)[0]
        headers = next(reader)
        rows = list(csv.DictReader(handle, fieldnames=headers))

    descriptions = {row["proposition"]: row["proof"] for row in rows}
    claim_labels = {
        row["proposition"]: f"From {row['speaker'].title()}: {row['proof']}"
        for row in rows
        if not row["number"].startswith("N")
    }
    return title, descriptions, claim_labels


def describe(formula: str, descriptions: dict[str, str]) -> str:
    if formula in descriptions:
        return descriptions[formula]
    if formula.startswith("~(") and formula.endswith(")"):
        return f"It is not the case that {describe(formula[2:-1], descriptions)}"
    if formula.startswith("~"):
        return f"It is not the case that {describe(formula[1:], descriptions)}"
    return formula


def parse_argument(argument: str) -> tuple[list[str], str]:
    match = re.fullmatch(r"\{(.*)\}\|-(.+)", argument)
    if not match:
        raise ValueError(f"Unexpected cached argument: {argument}")
    premises = [item.strip() for item in match.group(1).split(",") if item.strip()]
    return premises, match.group(2).strip()


def parse_premise_sets(encoded: str) -> list[list[str]]:
    return [
        [item.strip() for item in group.split(",") if item.strip()]
        for group in re.findall(r"\{([^{}]*)\}", encoded)
    ]


def load_claim(claim: str, descriptions: dict[str, str], claim_labels: dict[str, str]) -> dict:
    with (DATA_DIR / "cache_ext.txt").open(encoding="utf-8") as handle:
        extension_cache = json.load(handle)
    with (DATA_DIR / "cache_premises.txt").open(encoding="utf-8") as handle:
        premises_cache = json.load(handle)

    if claim not in extension_cache:
        raise KeyError(f"Claim is not present in cache_ext.txt: {claim}")

    extension = ast.literal_eval(extension_cache[claim].replace("set()", "'__empty_set__'"))
    premise_index = premises_cache.get(claim, {})

    nodes = []
    for index, raw_argument in enumerate(extension["original_arg"]):
        fallback_premises, conclusion = parse_argument(raw_argument)
        premise_sets = parse_premise_sets(premise_index.get(conclusion, "")) or [fallback_premises]
        nodes.append(
            {
                "id": index,
                "label": f"A{index + 1}",
                "raw": raw_argument,
                "conclusion": conclusion,
                "conclusionText": describe(conclusion, descriptions),
                "premiseSets": [
                    {
                        "formulas": formulas,
                        "descriptions": [describe(formula, descriptions) for formula in formulas],
                    }
                    for formulas in premise_sets
                ],
            }
        )

    return {
        "id": claim,
        "label": claim_labels.get(claim, describe(claim, descriptions)),
        "nodes": nodes,
        "edges": [
            {"source": source, "target": target}
            for source, target in extension["relation"]
        ],
    }


def export(output: Path, claim: str) -> None:
    title, descriptions, claim_labels = load_knowledge_base()
    payload = {
        "title": title,
        "note": "Static export of cached research-prototype data.",
        "claims": [load_claim(claim, descriptions, claim_labels)],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claim", default=DEFAULT_CLAIM)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    export(args.output, args.claim)


if __name__ == "__main__":
    main()
