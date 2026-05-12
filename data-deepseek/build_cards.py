#!/usr/bin/env python3
"""
Phase 2: Parse OCR full text → chapters → sections → knowledge cards.
Output follows content_package conventions.
"""
import os, json, re
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
TEXT_PATH = os.path.join(ROOT, 'ocr_output', 'full_text.txt')
CONTENT_OUT = os.path.join(ROOT, 'content_package', 'public')
SUBJECT_OUT = os.path.join(CONTENT_OUT, 'subjects', 'high_itpmp')
NOW = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')

os.makedirs(os.path.join(SUBJECT_OUT, 'chapters'), exist_ok=True)
os.makedirs(os.path.join(SUBJECT_OUT, 'questions'), exist_ok=True)

with open(TEXT_PATH, 'r', encoding='utf-8') as f:
    full_text = f.read()

# Remove page markers
full_text = re.sub(r'--- PAGE BREAK ---', '\n', full_text)
# Remove page number lines like "第1页" "第 100 页"
full_text = re.sub(r'第\s*\d+\s*页\s*', '\n', full_text)
# Remove watermark lines
full_text = re.sub(r'更多资料请咸[⻥魚]搜索\s*[:：]\s*环球课堂\s*', '', full_text)
# Normalize whitespace
full_text = re.sub(r'\n{3,}', '\n\n', full_text)

print(f"Cleaned text: {len(full_text)} chars")

# ── Split into chapters ──
# Only match chapter headers at logical boundaries
# Reject inline references like "详见第6章" or "本章(1)标题类知识点总结"
chapter_splits = []
for m in re.finditer(r'第\s*(\d{1,2})\s*章[-\s]*([^\n]{0,40})', full_text):
    # Check prefix: should be empty/page-break, not inline text
    prefix = full_text[max(0,m.start()-30):m.start()].strip()
    if prefix and any(kw in prefix for kw in ['本章', '详见', '参见', '见第', '泪及', '总主见']):
        continue
    chapter_splits.append(m)

# Deduplicate: keep only the first occurrence of each chapter number
seen_nums = set()
unique_splits = []
for m in chapter_splits:
    ch_num = int(m.group(1))
    if ch_num not in seen_nums:
        seen_nums.add(ch_num)
        unique_splits.append(m)
chapter_splits = unique_splits

chapters = []
for i, m in enumerate(chapter_splits):
    ch_num = int(m.group(1))
    ch_title = m.group(2).strip().lstrip('-~').strip().rstrip('。-—')
    start = m.start()
    end = chapter_splits[i+1].start() if i+1 < len(chapter_splits) else len(full_text)
    ch_text = full_text[start:end].strip()
    chapters.append({'num': ch_num, 'title': ch_title, 'text': ch_text})

print(f"Chapters found: {len(chapters)}")
for ch in chapters:
    print(f"  Ch {ch['num']:2d}: {ch['title'][:30]} ({len(ch['text'])} chars)")

# ── Chapter name mapping ──
CHAPTER_NAMES = {
    1: "信息化发展", 2: "信息技术发展", 3: "信息系统治理",
    4: "信息系统管理", 5: "信息系统工程", 6: "项目管理概论",
    7: "立项管理", 8: "整合管理", 9: "范围管理",
    10: "进度管理", 11: "成本管理", 12: "质量管理",
    13: "资源管理", 14: "沟通管理", 15: "风险管理",
    16: "采购管理", 17: "干系人管理", 18: "项目绩效域",
    19: "配置与变更管理", 20: "高级项目管理", 21: "项目管理科学基础",
    22: "组织通用治理", 23: "组织通用管理",
}

# ── Process each chapter into sections and cards ──
manifest_chapters = []
file_index_entries = []
total_cards = 0

for ch in chapters:
    ch_id = f"ch_{ch['num']:02d}"
    ch_name = CHAPTER_NAMES.get(ch['num'], ch['title'])
    ch_dir = os.path.join(SUBJECT_OUT, 'chapters', ch_id)
    cards_dir = os.path.join(ch_dir, 'cards')
    os.makedirs(cards_dir, exist_ok=True)

    text = ch['text']
    ch_cards = 0
    card_sort = 0
    sections_meta = []

    # Split into sections using "X.X" pattern
    section_splits = list(re.finditer(r'(?:^|\n)\s*(\d+)\s*[\.．]\s*(\d+)\s*([^\n]{0,60})', text))

    if not section_splits:
        # No explicit sections → treat entire chapter as one section
        section_splits = [None]  # sentinel
        sec_id = "sec_01"
        sections_to_process = [(sec_id, sec_title if 'sec_title' in dir() else ch_name, 0, len(text))]
    else:
        sections_to_process = []
        for si, sm in enumerate(section_splits):
            sec_minor = int(sm.group(2))
            sec_title = sm.group(3).strip()
            sec_id = f"sec_{sec_minor:02d}"
            sec_start = sm.start()
            sec_end = section_splits[si+1].start() if si+1 < len(section_splits) else len(text)
            sections_to_process.append((sec_id, sec_title, sec_start, sec_end))

    for sec_id, sec_title, sec_start, sec_end in sections_to_process:
        sec_text = text[sec_start:sec_end].strip() if sec_start > 0 or section_splits[0] is not None else text

        # Split into knowledge cards by numbered items
        card_splits = list(re.finditer(r'(?:^|\n)\s*(\d+)\s*[、．.]\s*', sec_text))

        sec_card_count = 0
        for ci, cm in enumerate(card_splits):
            card_start = cm.end()
            card_end = card_splits[ci+1].start() if ci+1 < len(card_splits) else len(sec_text)
            card_raw = sec_text[card_start:card_end].strip()

            if len(card_raw) < 15:  # Skip too-short items
                continue

            card_sort += 1
            sec_card_count += 1
            card_id = f"{card_sort:03d}"
            file_stem = f"{ch_id}_{sec_id}_{card_id}"

            # Extract title (first sentence or first line, trim)
            title_line = card_raw.split('\n')[0].strip()
            title_line = re.sub(r'[：:]\s*$', '', title_line)  # Remove trailing colon
            if len(title_line) > 50:
                title_line = title_line[:50]
            card_title = title_line or ch_name

            # Build card JSON
            card = {
                "point_id": card_id,
                "subject_id": "high_itpmp",
                "chapter_id": ch_id,
                "section_id": sec_id,
                "title": card_title,
                "card_type": "concept",
                "difficulty": 2,
                "estimated_read_seconds": max(60, len(card_raw) // 3),
                "has_key_content": '==' in card_raw,
                "is_free": True,
                "sort_no": card_sort,
                "content_file": f"{file_stem}.md",
                "tags": [ch_name, sec_title, card_title[:20]],
                "key_points": "",
                "mnemonics": "",
                "prerequisite_point_ids": [],
                "related_point_ids": [],
                "related_question_ids": [],
                "source": "2026新版高项三色笔记（信息系统项目管理师）",
                "source_type": "exam_note",
                "source_refs": [{
                    "source_id": "pdf_2026_tricolor_high",
                    "page_label": f"OCR自动定位-{ch_id}"
                }],
                "author": "Codex OCR 批量整理",
                "reviewer": "待人工复核",
                "review_status": "ai_draft",
                "created_at": NOW,
                "updated_at": NOW,
                "version": 1,
                "schema_version": 2,
                "warnings": "本卡片由 OCR 文本自动整理，review_status 为 ai_draft，上线前需人工核对。红色高亮待二期检测补充。"
            }

            # Format card body as Markdown
            md_body = f"### 概述\n\n{card_raw}\n"

            # Write files
            json_path = os.path.join(cards_dir, f"{file_stem}.json")
            md_path = os.path.join(cards_dir, f"{file_stem}.md")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_body)

            # Add to file index
            for ext, ct in [('.json', 'application/json; charset=utf-8'), ('.md', 'text/markdown; charset=utf-8')]:
                rel = f"subjects/high_itpmp/chapters/{ch_id}/cards/{file_stem}{ext}"
                fpath = os.path.join(SUBJECT_OUT, 'chapters', ch_id, 'cards', f"{file_stem}{ext}")
                file_index_entries.append({
                    "path": rel,
                    "bytes": os.path.getsize(fpath),
                    "sha256": "ocr-draft",
                    "content_type": ct
                })

        if sec_card_count > 0:
            sections_meta.append({
                "section_id": sec_id,
                "title": sec_title,
                "sort_no": len(sections_meta) + 1,
                "description": sec_title,
                "card_count": sec_card_count
            })
        ch_cards += sec_card_count

    # Write chapter_meta.json
    chapter_meta = {
        "chapter_id": ch_id,
        "subject_id": "high_itpmp",
        "title": ch_name,
        "description": f"围绕{ch_name}展开",
        "sort_no": ch['num'],
        "sections": sections_meta,
        "schema_version": 2
    }
    with open(os.path.join(ch_dir, 'chapter_meta.json'), 'w', encoding='utf-8') as f:
        json.dump(chapter_meta, f, ensure_ascii=False, indent=2)

    manifest_chapters.append({
        "chapter_id": ch_id,
        "title": ch_name,
        "card_count": ch_cards,
        "question_count": 0
    })

    total_cards += ch_cards
    print(f"  {ch_id} {ch_name}: {ch_cards} cards, {len(sections_meta)} sections")

# ── Write subject_index.json ──
subject_index = {
    "subject_id": "high_itpmp",
    "subject_name": "高级-信息系统项目管理师",
    "exam_version": "2026",
    "chapters": [
        {
            "chapter_id": c["chapter_id"],
            "title": c["title"],
            "sort_no": int(c["chapter_id"].split('_')[1]),
            "card_count": c["card_count"],
            "question_count": 0
        }
        for c in manifest_chapters
    ],
    "schema_version": 2
}
with open(os.path.join(SUBJECT_OUT, 'subject_index.json'), 'w', encoding='utf-8') as f:
    json.dump(subject_index, f, ensure_ascii=False, indent=2)

# ── Write manifest.json ──
manifest = {
    "package_id": "atomq_high_itpmp_2026_public_full",
    "subject_id": "high_itpmp",
    "content_version": f"{NOW[:10]}.full-ocr-draft.1.public-full",
    "generated_at": NOW,
    "source_ids": ["pdf_2026_tricolor_high"],
    "chapters": manifest_chapters,
    "storage_policy": {
        "static_content": "Aliyun OSS public-read",
        "dynamic_user_data": "SQLite locally",
        "paid_content": "Not separated; all static content is public-free."
    },
    "schema_version": 2,
    "distribution": {
        "mode": "public_read_full",
        "origin": "local",
        "file_index": "file_index.json",
        "app_cache_path": "Documents/cache/cards/content_package/public"
    }
}
with open(os.path.join(CONTENT_OUT, 'manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

# ── Write file_index.json ──
file_index = {
    "package_id": manifest["package_id"],
    "content_version": manifest["content_version"],
    "access": "public_read",
    "files": file_index_entries
}
with open(os.path.join(CONTENT_OUT, 'file_index.json'), 'w', encoding='utf-8') as f:
    json.dump(file_index, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print(f"Total: {total_cards} cards across {len(chapters)} chapters")
print(f"Output: {CONTENT_OUT}")
