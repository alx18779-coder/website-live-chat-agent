#!/usr/bin/env python3
"""
Preprocess the bilingual FAQ markdown into a structured JSONL file.

Each record contains:
{
    "section": "...",
    "question_zh": "...",
    "question_en": "...",
    "answer_zh": "...",
    "answer_en": "..."
}
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def split_bilingual(text: str) -> tuple[str, str]:
    """Split a `zh / en` string into (zh, en), respecting inline slashes like `L/min`."""
    marker = " / "
    if marker not in text:
        raise ValueError(f"Cannot find bilingual delimiter ' / ' in: {text!r}")
    zh, en = text.rsplit(marker, 1)
    return zh.strip(), en.strip()


def preprocess_faq(src: Path, dst: Path) -> None:
    data = []
    section = None
    question_zh = question_en = None

    for raw_line in src.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("####"):
            section = line.lstrip("#").strip()
            continue

        if line.startswith("Q:"):
            question_zh, question_en = split_bilingual(line[2:].strip())
            continue

        if line.startswith("A:"):
            if question_zh is None or question_en is None:
                raise RuntimeError(f"Answer encountered before question: {line}")

            answer_zh, answer_en = split_bilingual(line[2:].strip())
            data.append(
                {
                    "section": section,
                    "question_zh": question_zh,
                    "question_en": question_en,
                    "answer_zh": answer_zh,
                    "answer_en": answer_en,
                }
            )
            question_zh = question_en = None
            continue

    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    src_path = root / "evaluate" / "ragas" / "docs" / "faq.md"
    dst_path = root / "evaluate" / "ragas" / "processed" / "faq.jsonl"
    preprocess_faq(src_path, dst_path)
