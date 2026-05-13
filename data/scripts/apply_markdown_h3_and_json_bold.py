#!/usr/bin/env python3
"""Normalize public card markdown headings and JSON emphasis markers."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = ROOT / "content_package" / "public"
SUBJECT_ROOT = PUBLIC_ROOT / "subjects" / "high_itpmp"
CONTENT_VERSION = "2026.05.full-color-ocr-draft.4.h3-json-bold"
JSON_FIELDS = ("key_points", "mnemonics")


def replace_h4_with_h3(text: str) -> tuple[str, int]:
    return re.subn(r"(?m)^####(?!#)\s+", "### ", text)


def replace_json_highlight(text: str) -> tuple[str, int]:
    return re.subn(r"==([^=\n]+)==", r"**\1**", text)


def rewrite_md_files() -> tuple[int, int]:
    files_changed = 0
    replacements = 0
    for path in sorted(SUBJECT_ROOT.rglob("*.md")):
        original = path.read_text(encoding="utf-8")
        updated, count = replace_h4_with_h3(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            files_changed += 1
            replacements += count
    return files_changed, replacements


def rewrite_json_value(value: object) -> tuple[object, int, bool]:
    replacements = 0
    changed = False
    if isinstance(value, dict):
        updated_dict: dict[str, object] = {}
        for key, item in value.items():
            if key in JSON_FIELDS and isinstance(item, str):
                updated_item, count = replace_json_highlight(item)
                updated_dict[key] = updated_item
                replacements += count
                changed = changed or updated_item != item
            else:
                updated_item, count, item_changed = rewrite_json_value(item)
                updated_dict[key] = updated_item
                replacements += count
                changed = changed or item_changed
        return updated_dict, replacements, changed
    if isinstance(value, list):
        updated_list: list[object] = []
        for item in value:
            updated_item, count, item_changed = rewrite_json_value(item)
            updated_list.append(updated_item)
            replacements += count
            changed = changed or item_changed
        return updated_list, replacements, changed
    return value, 0, False


def rewrite_json_files() -> tuple[int, int]:
    files_changed = 0
    replacements = 0
    for path in sorted(SUBJECT_ROOT.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        updated_data, count, changed = rewrite_json_value(data)
        if changed:
            path.write_text(
                json.dumps(updated_data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            files_changed += 1
            replacements += count
    return files_changed, replacements


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh_manifest_and_index() -> tuple[int, int]:
    manifest_path = PUBLIC_ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["content_version"] = CONTENT_VERSION
    manifest["generated_at"] = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    files: list[dict[str, object]] = []
    for path in sorted(PUBLIC_ROOT.rglob("*")):
        if not path.is_file() or path.name == "file_index.json":
            continue
        rel = path.relative_to(PUBLIC_ROOT).as_posix()
        files.append(
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    file_index = {
        "package_id": manifest["package_id"],
        "content_version": manifest["content_version"],
        "file_count": len(files),
        "files": files,
    }
    index_path = PUBLIC_ROOT / "file_index.json"
    index_path.write_text(
        json.dumps(file_index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(files), index_path.stat().st_size


def main() -> None:
    md_files, md_replacements = rewrite_md_files()
    json_files, json_replacements = rewrite_json_files()
    indexed_files, index_bytes = refresh_manifest_and_index()
    print(f"md_files_changed={md_files}")
    print(f"md_h4_to_h3_replacements={md_replacements}")
    print(f"json_files_changed={json_files}")
    print(f"json_highlight_to_bold_replacements={json_replacements}")
    print(f"indexed_files={indexed_files}")
    print(f"file_index_bytes={index_bytes}")


if __name__ == "__main__":
    main()
