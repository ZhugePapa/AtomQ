#!/usr/bin/env python3
"""Refine chapters 2-23 into readable AI-draft study cards.

Chapter 1 is curated by rebuild_ch01_curated.py and is intentionally skipped.
This pass improves the previous bulk OCR draft without changing stable IDs:
- h3+ headings become h4+ in Markdown bodies.
- OCR boilerplate and motivational noise are removed.
- Markdown body is rebuilt as readable study content.
- ==highlight== is applied to repeated recall terms in lists/tables.
- key_points and mnemonics are treated as optional Markdown snippets.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = ROOT / "content_package" / "public"
SUBJECT_ID = "high_itpmp"
SUBJECT_ROOT = PUBLIC_ROOT / "subjects" / SUBJECT_ID
CHAPTERS_ROOT = SUBJECT_ROOT / "chapters"

NOISE_PATTERNS = [
    "本章学起来比较有难度",
    "学起来比较有难度",
    "确实不懂的把教材原文多读多看即可",
    "把握关键词进行记忆",
    "如果确实不想看",
    "我觉得本章也是可以放弃",
    "考前把发的考点看看就好",
    "是本章需要掌握的考点之一",
    "来自原始 PDF 的 OCR 识别结果",
    "需人工复核后发布",
]

TINY_HEADERS = {
    "要素",
    "具体内容",
    "内容",
    "过程",
    "步骤",
    "说明",
    "活动",
    "工具",
    "技术",
    "输出",
    "输入",
    "层次",
    "协议",
    "阶段",
    "类型",
    "分类",
    "特点",
    "名称",
}

IMPORTANT_HINTS = [
    "包括",
    "主要",
    "核心",
    "必须",
    "不是",
    "不能",
    "属于",
    "分为",
    "过程",
    "阶段",
    "输入",
    "输出",
    "工具",
    "技术",
    "目标",
    "原则",
    "特点",
    "模型",
    "体系",
    "要素",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def strip_highlight(text: str) -> str:
    return text.replace("==", "")


def split_highlight_segments(text: str) -> list[str]:
    return text.split("==")


def wrap_unhighlighted(text: str, needle: str, replacement: str | None = None) -> str:
    if not needle:
        return text
    replacement = replacement or f"=={needle}=="
    parts = split_highlight_segments(text)
    for index in range(0, len(parts), 2):
        parts[index] = parts[index].replace(needle, replacement)
    return "==".join(parts)


def downgrade_headings(md: str) -> str:
    out = []
    for line in md.splitlines():
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith("#"):
            hashes, _, rest = stripped.partition(" ")
            if hashes and set(hashes) == {"#"} and 1 <= len(hashes) < 6:
                out.append(f"{indent}{hashes}# {rest}")
                continue
        out.append(line)
    return "\n".join(out).strip() + "\n"


def normalize_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^[\-*]\s*", "", line)
    line = re.sub(r"\s+", " ", line)
    line = line.replace("0SI", "OSI")
    line = line.replace("，", "，")
    return line.strip()


def is_noise(line: str) -> bool:
    clean = strip_highlight(line)
    if not clean:
        return True
    if any(pattern in clean for pattern in NOISE_PATTERNS):
        return True
    if clean in TINY_HEADERS:
        return True
    if re.fullmatch(r"第?\d+\s*页", clean):
        return True
    if "更多资料请" in clean or "环球课堂" in clean:
        return True
    if clean.startswith("###") or clean.startswith("####") or clean.startswith("#"):
        return True
    if clean.startswith("<!--"):
        return True
    return False


def extract_lines(md: str) -> list[str]:
    raw_lines = [normalize_line(line) for line in md.splitlines()]
    lines = [line for line in raw_lines if not is_noise(line)]

    # Remove previous wrapper sentence if it survived around highlighted titles.
    filtered = []
    for line in lines:
        clean = strip_highlight(line)
        if "是本章需要掌握的考点之一" in clean:
            tail = clean.split("是本章需要掌握的考点之一", 1)[-1].strip("。 ：:")
            if tail and not is_noise(tail):
                filtered.append(tail)
            continue
        filtered.append(line)

    merged: list[str] = []
    for line in filtered:
        clean = strip_highlight(line)
        starts_item = bool(re.match(r"^(\d{1,2}|[一二三四五六七八九十]+)[、.．]\s*", clean))
        starts_bulletish = bool(re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", clean))
        has_label = bool(re.match(r"^[^：:]{2,20}[：:]", clean))
        if not merged or starts_item or starts_bulletish or has_label:
            merged.append(line)
            continue
        prev = merged[-1]
        if len(strip_highlight(prev)) < 28 and strip_highlight(prev) in TINY_HEADERS:
            merged[-1] = line
        elif not re.search(r"[。！？；;：:]$", strip_highlight(prev)) and len(strip_highlight(prev)) < 120:
            merged[-1] = prev + clean
        else:
            merged.append(line)

    result = []
    seen = set()
    for line in merged:
        clean = strip_highlight(line).strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        result.append(clean)
    return result


def clean_title(title: str, lines: list[str]) -> str:
    title = strip_highlight(title or "").strip()
    if any(pattern in title for pattern in NOISE_PATTERNS) or len(title) < 3:
        title = ""
    if not title and lines:
        title = lines[0]
    title = re.sub(r"^(\d{1,2}|[一二三四五六七八九十]+)[、.．]\s*", "", title)
    title = re.sub(r"[。；;，,].*$", "", title)
    title = title.strip(" ：:「」[]【】")
    if len(title) > 30:
        title = title[:30]
    return title or "章节考点"


def extract_label(line: str) -> tuple[str, str] | None:
    clean = strip_highlight(line).strip()
    clean = re.sub(r"^(\d{1,2}|[一二三四五六七八九十]+)[、.．]\s*", "", clean)
    match = re.match(r"^([^：:]{2,18})[：:]\s*(.+)$", clean)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None


def extract_labels(lines: list[str]) -> list[tuple[str, str]]:
    labels = []
    for line in lines:
        item = extract_label(line)
        if item and item[0] not in TINY_HEADERS:
            labels.append(item)
    dedup = []
    seen = set()
    for label, desc in labels:
        if label in seen:
            continue
        seen.add(label)
        dedup.append((label, desc))
    return dedup


def terms_from_enumeration(text: str) -> list[str]:
    clean = strip_highlight(text)
    match = re.search(r"(包括|分为|包含|主要有|主要包括)([^。；;]{6,80})", clean)
    if not match:
        return []
    fragment = match.group(2)
    raw_terms = re.split(r"[、,，/和及与]+", fragment)
    terms = []
    for term in raw_terms:
        term = term.strip(" ：:。；;（）()[]【】")
        if 2 <= len(term) <= 14 and not re.search(r"\d", term):
            terms.append(term)
    return terms[:10]


def highlight_line(line: str, title: str, labels: list[tuple[str, str]]) -> str:
    out = line
    title_clean = strip_highlight(title)
    if title_clean and title_clean in out and len(title_clean) <= 18:
        out = wrap_unhighlighted(out, title_clean)

    for label, _ in labels:
        out = wrap_unhighlighted(out, f"{label}：", f"=={label}==：")
        out = wrap_unhighlighted(out, f"{label}:", f"=={label}==:")

    for term in terms_from_enumeration(line):
        out = wrap_unhighlighted(out, term)

    # Highlight compact numbered item labels: "1、规划级：..."
    match = re.match(r"^((\d{1,2}|[一二三四五六七八九十]+)[、.．]\s*)([^：:]{2,14})([：:])", strip_highlight(out))
    if match:
        label = match.group(3).strip()
        out = wrap_unhighlighted(out, f"{label}{match.group(4)}", f"=={label}=={match.group(4)}")
    return out


def line_score(line: str) -> int:
    score = 0
    for hint in IMPORTANT_HINTS:
        if hint in line:
            score += 1
    if "==" in line:
        score += 2
    if re.match(r"^(\d{1,2}|[一二三四五六七八九十]+)[、.．]", line):
        score += 1
    return score


def make_markdown(title: str, lines: list[str]) -> str:
    labels = extract_labels(lines)
    overview_source = lines[0] if lines else title
    overview = highlight_line(overview_source, title, labels)

    body_lines = lines[1:] if len(lines) > 1 else []
    if not body_lines:
        body_lines = [overview_source]
    body_lines = body_lines[:12]
    highlighted = [highlight_line(line, title, labels) for line in body_lines]

    if labels and len(labels) >= 3:
        rows = []
        for label, desc in labels[:10]:
            rows.append(f"| =={label}== | {desc} |")
        core = "\n".join(["| 关键词 | 说明 |", "|:---|:---|", *rows])
    else:
        core = "\n".join(f"- {line}" for line in highlighted)

    grasp_candidates = sorted(lines, key=line_score, reverse=True)[:2]
    grasp = "\n".join(f"- {highlight_line(line, title, labels)}" for line in grasp_candidates if line_score(line) > 0)

    parts = [
        "#### 概述",
        "",
        overview,
        "",
        "#### 核心内容",
        "",
        core or f"- {overview}",
    ]
    if grasp:
        parts.extend(["", "#### 考试抓手", "", grasp])
    return "\n".join(parts).strip() + "\n"


def make_key_points(title: str, lines: list[str]) -> str:
    labels = extract_labels(lines)
    if 3 <= len(labels) <= 8:
        rows = [f"| =={label}== | {desc[:48]} |" for label, desc in labels]
        return "\n".join(["| 关键词 | 考点 |", "|:---|:---|", *rows])

    candidates = []
    for line in lines:
        if line_score(line) > 0 and len(strip_highlight(line)) >= 12:
            candidates.append(line)
        if len(candidates) >= 3:
            break
    if len(candidates) <= 1:
        return ""
    return "\n".join(f"- {highlight_line(line, title, labels)}" for line in candidates[:3])


def extract_mnemonic(lines: list[str], title: str) -> str:
    joined = "\n".join(lines)
    match = re.search(r"口诀[：:]\s*([^】\n。；;]{2,40})", joined)
    if match:
        return match.group(1).strip()

    labels = [label for label, _ in extract_labels(lines)]
    sequence_title = any(token in title for token in ["生命周期", "过程", "成熟度", "等级", "步骤", "阶段", "体系", "要素"])
    if sequence_title and 3 <= len(labels) <= 7 and all(2 <= len(label) <= 8 for label in labels):
        return "按顺序记：**" + "、".join(labels) + "**。"
    return ""


def update_file_index() -> None:
    files = []
    for path in sorted(PUBLIC_ROOT.rglob("*")):
        if path.is_file() and path.name != "file_index.json":
            files.append(
                {
                    "path": path.relative_to(PUBLIC_ROOT).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    write_json(
        PUBLIC_ROOT / "file_index.json",
        {
            "package_id": "atomq_high_itpmp_2026_public_full",
            "content_version": "2026.05.full-ocr-draft.1.public-full",
            "file_count": len(files),
            "files": files,
        },
    )


def main() -> None:
    changed_cards = 0
    for chapter_dir in sorted(CHAPTERS_ROOT.glob("ch_*")):
        chapter_id = chapter_dir.name
        if chapter_id == "ch_01":
            continue
        meta_path = chapter_dir / "chapter_meta.json"
        cards_dir = chapter_dir / "cards"
        if not meta_path.exists() or not cards_dir.exists():
            continue

        chapter_meta = load_json(meta_path)
        section_titles = {s["section_id"]: s.get("title", "") for s in chapter_meta.get("sections", [])}
        card_paths = sorted(cards_dir.glob("*.json"))

        for card_path in card_paths:
            card = load_json(card_path)
            md_path = cards_dir / card.get("content_file", card_path.with_suffix(".md").name)
            if not md_path.exists():
                md_path = card_path.with_suffix(".md")
            original_md = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
            lines = extract_lines(original_md)
            title = clean_title(card.get("title", ""), lines)
            markdown = make_markdown(title, lines)
            key_points = make_key_points(title, lines)
            mnemonics = extract_mnemonic(lines, title)

            card["title"] = title
            card["subject_id"] = SUBJECT_ID
            card["chapter_id"] = chapter_id
            card["section_id"] = card.get("section_id") or "sec_01"
            card["content_file"] = md_path.name
            card["content_md_path"] = f"subjects/{SUBJECT_ID}/chapters/{chapter_id}/cards/{md_path.name}"
            card["has_key_content"] = "==" in markdown
            card["estimated_read_seconds"] = max(75, min(300, round(len(markdown.replace("\n", "")) / 6)))
            card["key_points"] = key_points
            card["mnemonics"] = mnemonics
            card.setdefault("tags", [])
            base_tags = [
                chapter_meta.get("title", ""),
                section_titles.get(card["section_id"], ""),
                title,
            ]
            tags = []
            for tag in [*base_tags, *card.get("tags", [])]:
                tag = strip_highlight(str(tag)).strip()
                if tag and tag not in tags:
                    tags.append(tag[:18])
            card["tags"] = tags[:8]
            card.setdefault("prerequisite_point_ids", [])
            card.setdefault("related_point_ids", [])
            card.setdefault("related_question_ids", [])
            card.setdefault("common_mistakes", [])
            card["review_status"] = "ai_draft"

            write_json(card_path, card)
            md_path.write_text(markdown, encoding="utf-8")
            changed_cards += 1

        # Ensure root chapter count is present and section counts match files.
        chapter_meta["card_count"] = len(card_paths)
        section_counts = {s["section_id"]: 0 for s in chapter_meta.get("sections", [])}
        for card_path in card_paths:
            section_id = load_json(card_path).get("section_id")
            if section_id in section_counts:
                section_counts[section_id] += 1
        for section in chapter_meta.get("sections", []):
            section["card_count"] = section_counts.get(section["section_id"], section.get("card_count", 0))
        write_json(meta_path, chapter_meta)

    # Sync subject_index and manifest card counts from chapter_meta.
    subject_index_path = SUBJECT_ROOT / "subject_index.json"
    subject_index = load_json(subject_index_path)
    chapter_counts = {}
    for meta_path in CHAPTERS_ROOT.glob("ch_*/chapter_meta.json"):
        meta = load_json(meta_path)
        chapter_counts[meta["chapter_id"]] = meta.get("card_count", 0)
    for chapter in subject_index.get("chapters", []):
        if chapter["chapter_id"] in chapter_counts:
            chapter["card_count"] = chapter_counts[chapter["chapter_id"]]
    write_json(subject_index_path, subject_index)

    manifest_path = PUBLIC_ROOT / "manifest.json"
    manifest = load_json(manifest_path)
    for chapter in manifest.get("chapters", []):
        if chapter["chapter_id"] in chapter_counts:
            chapter["card_count"] = chapter_counts[chapter["chapter_id"]]
    write_json(manifest_path, manifest)

    update_file_index()
    print(f"Refined {changed_cards} cards in chapters 2-23")


if __name__ == "__main__":
    main()
