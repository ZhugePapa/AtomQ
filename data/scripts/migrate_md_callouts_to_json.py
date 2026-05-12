#!/usr/bin/env python3
"""Move card callout blocks from Markdown into adjacent JSON metadata.

Mappings:
- :::key     -> key_points
- :::tip     -> mnemonics
- :::warning -> warnings
"""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "content_package" / "subjects" / "high_itpmp"
CALLOUT_RE = re.compile(r"(?ms)^:::(key|tip|warning)[^\n]*\n(.*?)\n:::\s*")


def merge_text(existing: str, incoming: str) -> str:
    existing = (existing or "").strip()
    incoming = (incoming or "").strip()
    if not incoming:
        return existing
    if not existing:
        return incoming
    if existing == incoming or incoming in existing:
        return existing
    if existing in incoming:
        return incoming
    return f"{existing}\n\n{incoming}"


def migrate_pair(md_path: Path) -> bool:
    json_path = md_path.with_suffix(".json")
    if not json_path.exists():
        return False

    md = md_path.read_text(encoding="utf-8")
    matches = list(CALLOUT_RE.finditer(md))
    if not matches:
        return False

    card = json.loads(json_path.read_text(encoding="utf-8"))
    extracted: dict[str, list[str]] = {"key": [], "tip": [], "warning": []}

    for match in matches:
        kind = match.group(1)
        body = match.group(2).strip()
        if body:
            extracted[kind].append(body)

    if extracted["key"]:
        card["key_points"] = merge_text(card.get("key_points", ""), "\n\n".join(extracted["key"]))
    if extracted["tip"]:
        card["mnemonics"] = merge_text(card.get("mnemonics", ""), "\n\n".join(extracted["tip"]))
    if extracted["warning"]:
        card["warnings"] = merge_text(card.get("warnings", ""), "\n\n".join(extracted["warning"]))

    card["has_key_content"] = bool(re.search(r"==.+?==", md))

    md = CALLOUT_RE.sub("", md)
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"

    json_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(md, encoding="utf-8")
    return True


def main() -> None:
    updated = 0
    for md_path in sorted(ROOT.glob("chapters/*/cards/*.md")):
        if migrate_pair(md_path):
            updated += 1
    print(f"updated_cards={updated}")


if __name__ == "__main__":
    main()
