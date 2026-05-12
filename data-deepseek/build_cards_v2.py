#!/usr/bin/env python3
"""
Card builder v2 — matches reference content_package quality:
  - Short, focused MD: # title, ## 原文要点, ## 记忆抓手
  - key_points / mnemonics / common_mistakes as arrays
  - ==highlight== on key sentences
  - One card = one knowledge concept from OCR numbered items
"""
import os, json, re
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
TEXT_PATH = os.path.join(ROOT, 'ocr_output', 'full_text.txt')
CONTENT_OUT = os.path.join(ROOT, 'content_package', 'public')
SUBJECT_OUT = os.path.join(CONTENT_OUT, 'subjects', 'high_itpmp')
NOW = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')

# ── Text loading & cleaning ──
with open(TEXT_PATH, 'r', encoding='utf-8') as f:
    full_text = f.read()

def clean_text(text):
    """Remove OCR noise, watermarks, page numbers."""
    text = re.sub(r'--- PAGE BREAK ---', '\n', text)
    text = re.sub(r'第\s*\d+\s*页\s*', '', text)
    text = re.sub(r'更多资料请咸[⻥魚]搜索\s*[:：]\s*环球课堂\s*', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove section header lines like "1 信息与信息化" (OCR-dropped dots)
    text = re.sub(r'^\d+\s+\d+\s+[^\n]+\n', '', text, flags=re.MULTILINE)
    # Remove standalone section number lines like "1.1"
    text = re.sub(r'^\d+\.\d+\s*\n', '', text, flags=re.MULTILINE)
    # Fix common OCR errors
    text = text.replace('丰是', '不是')
    text = text.replace('葛基者', '奠基者')
    return text.strip()

full_text = clean_text(full_text)
print(f"Cleaned: {len(full_text)} chars")

# ── Chapter name mapping ──
CHAPTER_NAMES = {
    1:"信息化发展",2:"信息技术发展",3:"信息系统治理",4:"信息系统管理",
    5:"信息系统工程",6:"项目管理概论",7:"立项管理",8:"整合管理",
    9:"范围管理",10:"进度管理",11:"成本管理",12:"质量管理",
    13:"资源管理",14:"沟通管理",15:"风险管理",16:"采购管理",
    17:"干系人管理",18:"项目绩效域",19:"配置与变更管理",
    20:"高级项目管理",21:"项目管理科学基础",22:"组织通用治理",23:"组织通用管理",
}

# ── Split into chapters (only at real chapter boundaries) ──
chapter_splits = []
for m in re.finditer(r'第\s*(\d{1,2})\s*章[-\s]*([^\n]{0,50})', full_text):
    prefix = full_text[max(0,m.start()-30):m.start()].strip()
    if prefix and any(kw in prefix for kw in ['本章','详见','参见','见第','泪及','总主见']):
        continue
    chapter_splits.append(m)

# Deduplicate
seen = set()
chapter_splits = [m for m in chapter_splits if not (int(m.group(1)) in seen or seen.add(int(m.group(1))))]

# ── Helper: extract title from a numbered item ──
def extract_title(text, chapter_name=''):
    """Get concept name — prefer short key term over full sentence."""
    line = text.split('\n')[0].strip()
    line = re.sub(r'^\d+\s*[、．.]\s*', '', line)
    line = re.sub(r'[：:]\s*$', '', line)

    # Pattern: "XXX是指/就是/是/即/为/包括" → title = "XXX"
    m = re.match(r'(.{2,15})[是指即为包括]', line)
    if m:
        concept = m.group(1).strip().rstrip('，,。')
        if 2 <= len(concept) <= 25:
            # If concept is very short (like "信息"), add context from chapter
            return concept

    # Pattern: "XXX：YYY" → title = "XXX"
    if '：' in line or ':' in line:
        parts = re.split(r'[：:]', line, maxsplit=1)
        concept = parts[0].strip()
        if 3 <= len(concept) <= 25:
            return concept

    # Pattern: "XXX包括" → title = "XXX"
    if '包括' in line:
        concept = line.split('包括')[0].strip()
        if 3 <= len(concept) <= 25:
            return concept

    # Fallback: short meaningful prefix
    for sep in ['。', '，', '；']:
        if sep in line:
            p = line.split(sep)[0].strip()
            if 4 <= len(p) <= 30:
                return p

    if len(line) > 30:
        line = line[:30]
    return line or chapter_name or '知识点'

def should_merge(current_text, next_text):
    """Determine if next item should be merged into current card."""
    # Sub-markers (①, ②, ►, ▸) → merge
    if re.match(r'[①②③④⑤⑥⑦⑧⑨⑩►▸]', next_text.strip()):
        return True
    # Short items (< 50 chars) that don't start a new concept → merge
    if len(next_text) < 50 and not re.match(r'.{2,10}(是指|就是|定义|包括|包含)', next_text):
        return True
    # Continuation lines (start with lowercase-looking or connectors)
    if re.match(r'^[的这和那但而与或之也还就又才]', next_text.strip()):
        return True
    return False

def merge_items(items_texts):
    """Group related consecutive items into cards. Returns (merged_texts, group_indices)."""
    if not items_texts:
        return [], []
    groups = [[0]]  # indices into items_texts
    for i in range(1, len(items_texts)):
        if should_merge(items_texts[groups[-1][-1]], items_texts[i]):
            groups[-1].append(i)
        else:
            groups.append([i])
    merged = ['\n\n'.join(items_texts[i] for i in g) for g in groups]
    return merged, groups

def extract_key_points(text):
    """Extract key sentences for key_points array."""
    points = []
    # The first sentence is usually the core definition
    first = text.split('\n')[0].strip()
    first = re.sub(r'^\d+\s*[、．.]\s*', '', first)
    if len(first) > 5:
        points.append(first)
    # Look for exam references like (17上4)
    exam_refs = re.findall(r'\([^)]*\d+[上下]\d*[^)]*\)', text)
    for ref in exam_refs:
        # Find the sentence containing this ref
        for line in text.split('\n'):
            if ref in line:
                clean = re.sub(r'^\d+\s*[、．.]\s*', '', line.strip())
                if clean not in points and len(clean) > 5:
                    points.append(clean)
    return points[:3]  # Max 3 key points

def extract_mnemonics(text):
    """Extract memory aids / 口诀."""
    result = []
    # Pattern: "记忆口诀" or "口诀"
    for kw in ['口诀', '记忆', '巧记', '速记']:
        if kw in text:
            for line in text.split('\n'):
                if kw in line:
                    clean = re.sub(r'^\d+\s*[、．.]\s*', '', line.strip())
                    if clean and clean not in result:
                        result.append(clean)
    # Also capture rhyme-like patterns (short, rhythmic lines)
    return result

def extract_common_mistakes(text):
    """Extract 易错提示."""
    result = []
    for kw in ['易错', '注意', '误区', '不要混淆']:
        if kw in text:
            for line in text.split('\n'):
                if kw in line:
                    clean = re.sub(r'^\d+\s*[、．.]\s*', '', line.strip())
                    if clean and clean not in result:
                        result.append(clean)
    return result

def identify_card_type(text):
    """Heuristic card type detection."""
    if any(kw in text for kw in ['公式', '计算', '=']):
        return 'formula'
    if any(kw in text for kw in ['步骤', '流程', '过程', '阶段']):
        return 'process'
    if any(kw in text for kw in ['对比', '区别', '不同', 'vs']):
        return 'comparison'
    if any(kw in text for kw in ['定义', '是指', '指的是', '就是']):
        return 'definition'
    return 'concept'

# ── Process ──
os.makedirs(SUBJECT_OUT, exist_ok=True)
os.makedirs(os.path.join(SUBJECT_OUT, 'chapters'), exist_ok=True)
os.makedirs(os.path.join(SUBJECT_OUT, 'questions'), exist_ok=True)

manifest_chapters = []
file_index_entries = []
total_cards = 0

for i, m in enumerate(chapter_splits):
    ch_num = int(m.group(1))
    ch_title_raw = m.group(2).strip().lstrip('-~').strip().rstrip('。-—')
    ch_name = CHAPTER_NAMES.get(ch_num, ch_title_raw)
    ch_id = f"ch_{ch_num:02d}"

    ch_start = m.start()
    ch_end = chapter_splits[i+1].start() if i+1 < len(chapter_splits) else len(full_text)
    ch_text = full_text[ch_start:ch_end].strip()

    # ── Split into numbered items, then merge related ones ──
    items = list(re.finditer(r'(?:^|\n)\s*(\d+)\s*[、．.]\s*', ch_text))

    if len(items) < 2:
        continue

    # Extract raw item texts WITH positions
    raw_items = []  # (text, position)
    for ii, im in enumerate(items):
        item_start = im.end()
        item_end = items[ii+1].start() if ii+1 < len(items) else len(ch_text)
        item_text = ch_text[item_start:item_end].strip()
        if len(item_text) >= 20:
            raw_items.append((item_text, im.start()))

    # Merge related items, keeping position of first item in group
    item_texts = [t for t, _ in raw_items]
    item_positions = [p for _, p in raw_items]
    merged_texts, groups = merge_items(item_texts)

    # Position of each merged card = position of first original item in group
    merged_positions = [item_positions[g[0]] for g in groups]

    print(f"  {ch_id}: {len(raw_items)} items → {len(merged_texts)} cards")

    ch_cards = []
    for gi, item_text in enumerate(merged_texts):
        title = extract_title(item_text, ch_name)
        key_points = extract_key_points(item_text)
        mnemonics = extract_mnemonics(item_text)
        common_mistakes = extract_common_mistakes(item_text)
        card_type = identify_card_type(item_text)

        # Build card
        sort_no = len(ch_cards) + 1
        card_id = f"{sort_no:03d}"

        # Determine section: closest preceding X.X marker
        sec_id = "sec_01"
        sec_title = ch_name
        pos = merged_positions[gi] if gi < len(merged_positions) else 0
        pre_text = ch_text[:pos]
        all_secs = list(re.finditer(r'(?:^|\n)\s*(\d+)\s*[\.．]\s*(\d+)\s*([^\n]{0,40})', pre_text))
        if all_secs:
            sm = all_secs[-1]
            sec_minor = int(sm.group(2))
            sec_id = f"sec_{sec_minor:02d}"
            sec_title = sm.group(3).strip() or ch_name

        file_stem = f"{ch_id}_{sec_id}_{card_id}"

        card = {
            "point_id": card_id,
            "subject_id": "high_itpmp",
            "chapter_id": ch_id,
            "section_id": sec_id,
            "title": title,
            "card_type": card_type,
            "difficulty": 2,
            "estimated_read_seconds": max(30, len(item_text) // 4),
            "has_key_content": True,
            "is_free": True,
            "sort_no": sort_no,
            "tags": [ch_name],
            "key_points": key_points,
            "mnemonics": mnemonics,
            "common_mistakes": common_mistakes,
            "review_status": "ai_draft",
            "content_file": f"{file_stem}.md",
            "content_md_path": f"subjects/high_itpmp/chapters/{ch_id}/cards/{file_stem}.md",
            "source_refs": [{
                "source": "2026新版高项三色笔记（信息系统项目管理师）",
                "location": f"OCR自动定位-{ch_id}"
            }]
        }

        # Build MD content
        md_lines = [f"# {title}", "", "## 原文要点", ""]
        # Split item text into clean paragraphs
        paragraphs = [p.strip() for p in item_text.split('\n') if p.strip()]
        for p in paragraphs:
            p = re.sub(r'^\d+\s*[、．.]\s*', '', p)  # Remove item number
            # Add ==highlight== to first key sentence
            if p == key_points[0] if key_points else False:
                md_lines.append(f"- =={p}==")
            else:
                md_lines.append(f"- {p}")
        md_body = '\n'.join(md_lines)

        # Write files
        cards_dir = os.path.join(SUBJECT_OUT, 'chapters', ch_id, 'cards')
        os.makedirs(cards_dir, exist_ok=True)
        json_path = os.path.join(cards_dir, f"{file_stem}.json")
        md_path = os.path.join(cards_dir, f"{file_stem}.md")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_body)

        ch_cards.append(card)
        total_cards += 1

        # File index
        for ext, ct in [('.json', 'application/json; charset=utf-8'), ('.md', 'text/markdown; charset=utf-8')]:
            fpath = os.path.join(cards_dir, f"{file_stem}{ext}")
            if os.path.exists(fpath):
                file_index_entries.append({
                    "path": f"subjects/high_itpmp/chapters/{ch_id}/cards/{file_stem}{ext}",
                    "bytes": os.path.getsize(fpath),
                    "sha256": "ocr-draft",
                    "content_type": ct
                })

    # Build sections from discovered section headers
    sec_pattern = re.finditer(r'(?:^|\n)\s*(\d+)\s*[\.．]\s*(\d+)\s*([^\n]{0,40})', ch_text)
    sections_meta = []
    seen_sec = set()
    for sm in sec_pattern:
        sec_minor = int(sm.group(2))
        sec_id = f"sec_{sec_minor:02d}"
        if sec_id in seen_sec:
            continue
        seen_sec.add(sec_id)
        sec_title = sm.group(3).strip() or ch_name
        sec_cards = sum(1 for c in ch_cards if c['section_id'] == sec_id)
        if sec_cards > 0:
            sections_meta.append({
                "section_id": sec_id,
                "title": sec_title,
                "sort_no": len(sections_meta) + 1,
                "description": sec_title,
                "card_count": sec_cards
            })
    # If no sections found, create default
    if not sections_meta:
        sections_meta = [{
            "section_id": "sec_01",
            "title": ch_name,
            "sort_no": 1,
            "description": ch_name,
            "card_count": len(ch_cards)
        }]
    # Fix section assignment for cards without a matching section
    for c in ch_cards:
        if not any(s['section_id'] == c['section_id'] for s in sections_meta):
            c['section_id'] = sections_meta[0]['section_id']
            # Update file paths
            old_stem = c['content_file'].replace('.md', '')
            new_stem = f"{ch_id}_{sections_meta[0]['section_id']}_{c['point_id']}"
            # Rename files if they exist
            cards_dir = os.path.join(SUBJECT_OUT, 'chapters', ch_id, 'cards')
            for ext in ['.json', '.md']:
                old_path = os.path.join(cards_dir, f"{old_stem}{ext}")
                new_path = os.path.join(cards_dir, f"{new_stem}{ext}")
                if os.path.exists(old_path) and old_path != new_path:
                    os.rename(old_path, new_path)
            c['content_file'] = f"{new_stem}.md"
            c['content_md_path'] = f"subjects/high_itpmp/chapters/{ch_id}/cards/{new_stem}.md"

    # Write chapter_meta.json
    chapter_meta = {
        "chapter_id": ch_id,
        "subject_id": "high_itpmp",
        "title": ch_name,
        "description": f"围绕{ch_name}展开",
        "sort_no": ch_num,
        "sections": sections_meta,
        "schema_version": 2
    }
    ch_dir = os.path.join(SUBJECT_OUT, 'chapters', ch_id)
    with open(os.path.join(ch_dir, 'chapter_meta.json'), 'w', encoding='utf-8') as f:
        json.dump(chapter_meta, f, ensure_ascii=False, indent=2)

    manifest_chapters.append({
        "chapter_id": ch_id,
        "title": ch_name,
        "card_count": len(ch_cards),
        "question_count": 0
    })

    print(f"  {ch_id} {ch_name}: {len(ch_cards)} cards")

# ── Write top-level files ──
subject_index = {
    "subject_id": "high_itpmp",
    "subject_name": "高级-信息系统项目管理师",
    "exam_version": "2026",
    "chapters": [{
        "chapter_id": c["chapter_id"],
        "title": c["title"],
        "sort_no": int(c["chapter_id"].split('_')[1]),
        "card_count": c["card_count"],
        "question_count": 0
    } for c in manifest_chapters],
    "schema_version": 2
}
with open(os.path.join(SUBJECT_OUT, 'subject_index.json'), 'w', encoding='utf-8') as f:
    json.dump(subject_index, f, ensure_ascii=False, indent=2)

manifest = {
    "package_id": "atomq_high_itpmp_2026_public_full",
    "subject_id": "high_itpmp",
    "content_version": f"{NOW[:10]}.full-ocr-draft.2.public-full",
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

file_index = {
    "package_id": manifest["package_id"],
    "content_version": manifest["content_version"],
    "access": "public_read",
    "files": file_index_entries
}
with open(os.path.join(CONTENT_OUT, 'file_index.json'), 'w', encoding='utf-8') as f:
    json.dump(file_index, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print(f"Total: {total_cards} cards across {len(manifest_chapters)} chapters")
print(f"Output: {CONTENT_OUT}")
