#!/usr/bin/env python3
"""
Card builder v3 — aggressive merging, smarter titles, mnemonic extraction.
No API needed. Pure heuristics tuned for the 三色笔记 format.
"""
import os, json, re
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
TEXT_PATH = os.path.join(ROOT, 'ocr_output', 'full_text.txt')
CONTENT_OUT = os.path.join(ROOT, 'content_package', 'public')
SUBJECT_OUT = os.path.join(CONTENT_OUT, 'subjects', 'high_itpmp')
NOW = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')

# ── Load & clean ──
with open(TEXT_PATH, 'r', encoding='utf-8') as f:
    full_text = f.read()

def clean_text(text):
    text = re.sub(r'--- PAGE BREAK ---', '\n', text)
    text = re.sub(r'第\s*\d+\s*页\s*', '', text)
    text = re.sub(r'更多资料请咸[⻥魚]搜索\s*[:：]\s*环球课堂\s*', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'^\d+\.\d+\s*\n', '', text, flags=re.MULTILINE)
    for old, new in [('丰是','不是'),('葛基者','奠基者'),('全软件只','硬件、软件、'),('泪及','涉及')]:
        text = text.replace(old, new)
    return text.strip()

full_text = clean_text(full_text)

# ── Chapters ──
CHAPTER_NAMES = {
    1:"信息化发展",2:"信息技术发展",3:"信息系统治理",4:"信息系统管理",
    5:"信息系统工程",6:"项目管理概论",7:"立项管理",8:"整合管理",
    9:"范围管理",10:"进度管理",11:"成本管理",12:"质量管理",
    13:"资源管理",14:"沟通管理",15:"风险管理",16:"采购管理",
    17:"干系人管理",18:"项目绩效域",19:"配置与变更管理",
    20:"高级项目管理",21:"项目管理科学基础",22:"组织通用治理",23:"组织通用管理",
}

chapter_splits = []
for m in re.finditer(r'第\s*(\d{1,2})\s*章[-\s]*([^\n]{0,50})', full_text):
    prefix = full_text[max(0,m.start()-30):m.start()].strip()
    if prefix and any(kw in prefix for kw in ['本章','详见','参见','见第','泪及','总主见']):
        continue
    chapter_splits.append(m)

seen = set()
chapter_splits = [m for m in chapter_splits if not (int(m.group(1)) in seen or seen.add(int(m.group(1))))]

# ── Merge logic ──
def should_merge(current, next_item):
    """Return True if next item should be merged into current card."""
    # Sub-markers → always merge
    if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩►▸\-—]', next_item.strip()):
        return True
    # Very short items (<50 chars) after a substantial item → merge
    if len(next_item) < 50 and len(current) > 50:
        return True
    # Next item starts with "其中"、"即"、"也就是" → merge
    if re.match(r'^(其中|即|也就是|换句话|简单说|具体|包括|主要)', next_item.strip()):
        return True
    # Next item is clearly about the SAME concept (same leading keyword)
    cur_concept = re.match(r'^(.{2,15})[是指即为包括]', current)
    next_concept = re.match(r'^(.{2,15})[是指即为包括]', next_item)
    if cur_concept and next_concept and cur_concept.group(1) == next_concept.group(1):
        return True
    # Next item starts with lowercase-like continuation
    if re.match(r'^[的这和那但而与或之也还就又才了对过到在从]', next_item.strip()):
        return True
    return False

def merge_items(items):
    if not items: return [], []
    groups = [[0]]
    for i in range(1, len(items)):
        if should_merge(items[groups[-1][-1]], items[i]):
            groups[-1].append(i)
        else:
            groups.append([i])
    merged = ['\n\n'.join(items[i] for i in g) for g in groups]
    return merged, groups

# ── Card field extraction ──
def extract_title(text, section_title=''):
    """Get a short concept title."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines: return section_title or '知识点'
    first = lines[0]
    first = re.sub(r'^\d+\s*[、．.]\s*', '', first)

    # "XXX是/指/即/为/包括YYY" → "XXX"
    m = re.match(r'(.{2,20})[是指即为包括]', first)
    if m:
        c = m.group(1).strip().rstrip('，,。')
        if 2 <= len(c) <= 25:
            return c

    # "XXX：YYY" → "XXX"
    if '：' in first or ':' in first:
        c = re.split(r'[：:]', first)[0].strip()
        if 3 <= len(c) <= 25:
            return c

    # Fallback: first 25 chars
    for sep in '。，；':
        if sep in first:
            first = first.split(sep)[0]
            break
    if len(first) > 25:
        first = first[:25]
    return first or section_title or '知识点'

def extract_key_points(text):
    """Core definition sentences."""
    pts = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines:
        line = re.sub(r'^\d+\s*[、．.]\s*', '', line)
        # Definition pattern
        if re.search(r'[是指即为]', line) and len(line) > 10:
            pts.append(line)
            if len(pts) >= 2: break
    if not pts and lines:
        pts.append(lines[0])
    return pts[:2]

def extract_mnemonics(text):
    """Extract 口诀 from 【bracket】 patterns."""
    mn = []
    for m in re.finditer(r'【[^】]*(?:口诀|记忆|诀|记)[^】]*】', text):
        mn.append(m.group(0).strip('【】'))
    # Also look for parenthesized memory aids
    for m in re.finditer(r'（[^）]*(?:口诀|记忆|巧记)[^）]*）', text):
        mn.append(m.group(0).strip('（）'))
    # Short rhyming lines
    short_lines = [l for l in text.split('\n') if 5 <= len(l.strip()) <= 30 and '，' not in l]
    for line in short_lines:
        if re.search(r'[，,]', line) and len(line) < 35:
            pass  # Skip multi-clause
    return mn[:2]

def extract_common_mistakes(text):
    ms = []
    for m in re.finditer(r'【[^】]*(?:易错|注意|误区|不要)[^】]*】', text):
        ms.append(m.group(0).strip('【】'))
    return ms[:2]

def card_type(text):
    if any(kw in text for kw in ['公式','计算','=']): return 'formula'
    if any(kw in text for kw in ['步骤','流程','阶段','周期','过程']): return 'process'
    if any(kw in text for kw in ['对比','区别','不同','vs','差异']): return 'comparison'
    if any(kw in text for kw in ['定义','是指','指的是','就是','概念']): return 'definition'
    return 'concept'

# ── Main ──
os.makedirs(SUBJECT_OUT, exist_ok=True)
manifest_chapters = []
file_index = []
total = 0

for i, m in enumerate(chapter_splits):
    ch_num = int(m.group(1))
    ch_name = CHAPTER_NAMES.get(ch_num, m.group(2).strip().lstrip('-~ '))
    ch_id = f"ch_{ch_num:02d}"
    ch_start = m.start()
    ch_end = chapter_splits[i+1].start() if i+1 < len(chapter_splits) else len(full_text)
    ch_text = full_text[ch_start:ch_end].strip()

    # ── Find section markers ──
    sec_markers = list(re.finditer(r'(?:^|\n)\s*(\d+)\s*[\.．]\s*(\d+)\s*([^\n]{0,50})', ch_text))

    # ── Split into numbered items ──
    items = list(re.finditer(r'(?:^|\n)\s*(\d+)\s*[、．.]\s*', ch_text))
    if len(items) < 2: continue

    # Group items by section
    item_data = []  # (text, sec_id, sec_title)
    for ii, im in enumerate(items):
        start = im.end()
        end = items[ii+1].start() if ii+1 < len(items) else len(ch_text)
        text = ch_text[start:end].strip()
        if len(text) < 15: continue

        # Find preceding section
        pos = im.start()
        sec_id, sec_title = "sec_01", ch_name
        for sm in sec_markers:
            if sm.start() < pos:
                sec_id = f"sec_{int(sm.group(2)):02d}"
                sec_title = sm.group(3).strip() or ch_name
        item_data.append((text, sec_id, sec_title))

    # ── Merge within each section ──
    cards = []
    for sec_id in sorted(set(d[1] for d in item_data), key=lambda x: int(x.split('_')[1])):
        sec_items = [d for d in item_data if d[1] == sec_id]
        if not sec_items: continue
        sec_title = sec_items[0][2]
        texts = [t for t, _, _ in sec_items]
        merged, groups = merge_items(texts)

        for gi, g in enumerate(groups):
            card_text = '\n\n'.join(texts[i] for i in g)
            title = extract_title(card_text, sec_title)
            kp = extract_key_points(card_text)
            mn = extract_mnemonics(card_text)
            cm = extract_common_mistakes(card_text)
            ct = card_type(card_text)

            sort_no = len(cards) + 1
            cid = f"{sort_no:03d}"
            stem = f"{ch_id}_{sec_id}_{cid}"
            md_lines = [f"# {title}", "", "## 原文要点", ""]

            # Build MD body with ==highlight==
            for line in card_text.split('\n'):
                line = line.strip()
                if not line: continue
                line = re.sub(r'^\d+\s*[、．.]\s*', '', line)
                # Highlight: if line is in key_points, wrap with ==
                is_key = any(k in line for k in kp) if kp else False
                if is_key and '==' not in line:
                    # Find the key sentence fragment and wrap it
                    for k in kp:
                        if k in line:
                            line = line.replace(k, f'=={k}==')
                            break
                md_lines.append(f"- {line}")

            md_body = '\n'.join(md_lines)

            card = {
                "point_id": cid, "subject_id": "high_itpmp",
                "chapter_id": ch_id, "section_id": sec_id,
                "title": title, "card_type": ct,
                "difficulty": 2, "estimated_read_seconds": max(30, len(card_text)//4),
                "has_key_content": '==' in md_body, "is_free": True,
                "sort_no": sort_no, "tags": [ch_name, sec_title],
                "key_points": kp, "mnemonics": mn, "common_mistakes": cm,
                "review_status": "ai_draft",
                "content_file": f"{stem}.md",
                "content_md_path": f"subjects/high_itpmp/chapters/{ch_id}/cards/{stem}.md",
                "source_refs": [{"source":"2026新版高项三色笔记","location":ch_id}]
            }

            cards_dir = os.path.join(SUBJECT_OUT, 'chapters', ch_id, 'cards')
            os.makedirs(cards_dir, exist_ok=True)
            with open(os.path.join(cards_dir, f"{stem}.json"), 'w', encoding='utf-8') as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            with open(os.path.join(cards_dir, f"{stem}.md"), 'w', encoding='utf-8') as f:
                f.write(md_body)

            cards.append(card)
            total += 1

    # ── Chapter meta ──
    sections_meta = []
    for sec_id in sorted(set(c['section_id'] for c in cards), key=lambda x: int(x.split('_')[1])):
        sec_cards = [c for c in cards if c['section_id'] == sec_id]
        title = sec_cards[0].get('tags',[''])[1] if len(sec_cards[0].get('tags',[])) > 1 else ch_name
        sections_meta.append({
            "section_id": sec_id, "title": title, "sort_no": len(sections_meta)+1,
            "description": title, "card_count": len(sec_cards)
        })

    ch_dir = os.path.join(SUBJECT_OUT, 'chapters', ch_id)
    with open(os.path.join(ch_dir, 'chapter_meta.json'), 'w', encoding='utf-8') as f:
        json.dump({"chapter_id":ch_id,"subject_id":"high_itpmp","title":ch_name,
                   "description":f"围绕{ch_name}展开","sort_no":ch_num,
                   "sections":sections_meta,"schema_version":2}, f, ensure_ascii=False, indent=2)

    manifest_chapters.append({"chapter_id":ch_id,"title":ch_name,"card_count":len(cards),"question_count":0})
    print(f"  {ch_id} {ch_name}: {len(cards)} cards, {len(sections_meta)} sections")

    # File index entries
    for c in cards:
        for ext, ct in [('.json','application/json; charset=utf-8'),('.md','text/markdown; charset=utf-8')]:
            fpath = os.path.join(SUBJECT_OUT, 'chapters', ch_id, 'cards', c['content_file'].replace('.md', ext))
            if os.path.exists(fpath):
                file_index.append({"path":f"subjects/high_itpmp/chapters/{ch_id}/cards/{c['content_file'].replace('.md', ext)}",
                                   "bytes":os.path.getsize(fpath),"sha256":"v3","content_type":ct})

# ── Top-level files ──
subject_index = {"subject_id":"high_itpmp","subject_name":"高级-信息系统项目管理师","exam_version":"2026",
    "chapters":[{"chapter_id":c["chapter_id"],"title":c["title"],
                 "sort_no":int(c["chapter_id"].split('_')[1]),"card_count":c["card_count"],"question_count":0}
                for c in manifest_chapters],"schema_version":2}
with open(os.path.join(SUBJECT_OUT, 'subject_index.json'), 'w', encoding='utf-8') as f:
    json.dump(subject_index, f, ensure_ascii=False, indent=2)

manifest = {"package_id":"atomq_high_itpmp_2026_public_full","subject_id":"high_itpmp",
    "content_version":f"{NOW[:10]}.v3.public-full","generated_at":NOW,
    "source_ids":["pdf_2026_tricolor_high"],"chapters":manifest_chapters,
    "schema_version":2,
    "distribution":{"mode":"public_read_full","origin":"local","file_index":"file_index.json"}}
with open(os.path.join(CONTENT_OUT, 'manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
with open(os.path.join(CONTENT_OUT, 'file_index.json'), 'w', encoding='utf-8') as f:
    json.dump({"package_id":manifest["package_id"],"content_version":manifest["content_version"],
               "access":"public_read","files":file_index}, f, ensure_ascii=False, indent=2)

print(f"\nTotal: {total} cards across {len(manifest_chapters)} chapters")
