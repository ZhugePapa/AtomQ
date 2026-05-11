#!/usr/bin/env python3
"""Validate AtomQ static content package consistency."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "content_package"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    subject_dirs = sorted((PACKAGE_ROOT / "subjects").glob("*"))
    if not subject_dirs:
        errors.append("No subject directories found.")

    for subject_dir in subject_dirs:
        subject_index_path = subject_dir / "subject_index.json"
        if not subject_index_path.exists():
            errors.append(f"Missing {subject_index_path}")
            continue

        subject_index = load_json(subject_index_path)
        all_cards: dict[tuple[str, str], Path] = {}
        chapter_cards: dict[str, set[str]] = {}

        for chapter in subject_index.get("chapters", []):
            chapter_id = chapter["chapter_id"]
            chapter_dir = subject_dir / "chapters" / chapter_id
            chapter_meta_path = chapter_dir / "chapter_meta.json"
            cards_dir = chapter_dir / "cards"

            if not chapter_meta_path.exists():
                errors.append(f"Missing chapter_meta for {chapter_id}")
                continue
            chapter_meta = load_json(chapter_meta_path)
            section_ids = {section["section_id"] for section in chapter_meta.get("sections", [])}

            card_paths = sorted(cards_dir.glob("*.json"))
            if chapter.get("card_count") != len(card_paths):
                errors.append(f"{chapter_id}: subject_index card_count={chapter.get('card_count')} actual={len(card_paths)}")

            section_counts = {section_id: 0 for section_id in section_ids}
            for card_path in card_paths:
                card = load_json(card_path)
                point_id = card.get("point_id")
                all_cards[(chapter_id, point_id)] = card_path
                chapter_cards.setdefault(chapter_id, set()).add(point_id)

                section_id = card.get("section_id")
                if section_id not in section_ids:
                    errors.append(f"{card_path}: section_id {section_id} not declared in chapter_meta")
                else:
                    section_counts[section_id] += 1

                expected_stem = f"{chapter_id}_{section_id}_{point_id}"
                if card_path.stem != expected_stem:
                    errors.append(f"{card_path}: expected filename stem {expected_stem}")

                md_path = cards_dir / card.get("content_file", "")
                if not md_path.exists():
                    errors.append(f"{card_path}: missing markdown file {card.get('content_file')}")
                else:
                    md_text = md_path.read_text(encoding="utf-8")
                    has_highlight = "==" in md_text
                    if bool(card.get("has_key_content")) != has_highlight:
                        errors.append(f"{card_path}: has_key_content={card.get('has_key_content')} but highlight_present={has_highlight}")

                if card.get("review_status") != "approved":
                    warnings.append(f"{point_id}: review_status={card.get('review_status')} needs human review before publishing")

            for section in chapter_meta.get("sections", []):
                expected = section.get("card_count")
                actual = section_counts.get(section["section_id"], 0)
                if expected != actual:
                    errors.append(f"{chapter_id}/{section['section_id']}: card_count={expected} actual={actual}")

        question_ids: set[str] = set()
        for question_file in sorted((subject_dir / "questions").glob("*.json")):
            questions = load_json(question_file)
            if not isinstance(questions, list):
                errors.append(f"{question_file}: expected array")
                continue
            for question in questions:
                qid = question.get("question_id")
                if qid in question_ids:
                    errors.append(f"Duplicate question_id {qid}")
                question_ids.add(qid)

                refs = question.get("knowledge_point_ids", [])
                if not refs:
                    errors.append(f"{qid}: missing knowledge_point_ids")
                primary_count = 0
                for ref in refs:
                    point_id = ref.get("point_id") if isinstance(ref, dict) else ref
                    chapter_id = question.get("chapter_id")
                    if (chapter_id, point_id) not in all_cards:
                        errors.append(f"{qid}: references missing point {point_id}")
                    if isinstance(ref, dict) and ref.get("is_primary"):
                        primary_count += 1
                if primary_count != 1:
                    errors.append(f"{qid}: expected exactly one primary knowledge point, got {primary_count}")

                for field in ["stem", "options", "answer", "analysis", "domain_tags"]:
                    if not question.get(field):
                        errors.append(f"{qid}: missing {field}")

        for (chapter_id, point_id), card_path in all_cards.items():
            card = load_json(card_path)
            for related_id in card.get("related_point_ids", []):
                if related_id not in chapter_cards.get(chapter_id, set()):
                    errors.append(f"{point_id}: related_point_id missing {related_id}")
            for prerequisite_id in card.get("prerequisite_point_ids", []):
                if prerequisite_id not in chapter_cards.get(chapter_id, set()):
                    errors.append(f"{point_id}: prerequisite_point_id missing {prerequisite_id}")
            for qid in card.get("related_question_ids", []):
                if qid not in question_ids:
                    errors.append(f"{point_id}: related_question_id missing {qid}")

    report = {
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
