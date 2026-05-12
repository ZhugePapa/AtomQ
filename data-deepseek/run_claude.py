#!/usr/bin/env python3
"""Call Claude via local desktop proxy to structure OCR text into cards."""
import os, json, re, urllib.request, time

API_URL = "http://127.0.0.1:15721/v1/messages"
API_TOKEN = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")

PROMPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CLAUDE_PROMPT.md")
OCR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_output")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content_package", "public", "subjects", "high_itpmp")

with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    PROMPT_TEMPLATE = f.read()

# ── Load OCR full text, split by chapter ──
with open(os.path.join(OCR_DIR, 'full_text.txt'), 'r', encoding='utf-8') as f:
    full_text = f.read()

# Split into per-chapter texts
chapter_texts = {}
for m in re.finditer(r'第\s*(\d{1,2})\s*章[-\s]*([^\n]{0,50})', full_text):
    prefix = full_text[max(0,m.start()-30):m.start()].strip()
    if prefix and any(kw in prefix for kw in ['本章','详见','参见','见第']):
        continue
    ch_num = int(m.group(1))
    if ch_num in chapter_texts:  # dedup
        continue
    chapter_texts[ch_num] = m  # store match object

# ── Process each chapter ──
def call_claude(chapter_text):
    """Send chapter OCR text to Claude, get structured cards."""
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 32000,
        "messages": [{
            "role": "user",
            "content": PROMPT_TEMPLATE + "\n\n---\n\n以下是需要处理的 OCR 文本：\n\n" + chapter_text
        }]
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_TOKEN,
            "anthropic-version": "2023-06-01"
        }
    )
    resp = urllib.request.urlopen(req, timeout=300)
    return json.loads(resp.read())

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'chapters'), exist_ok=True)

# Sort chapters
ch_nums = sorted(chapter_texts.keys())
print(f"Processing {len(ch_nums)} chapters: {ch_nums}")

for ch_num in ch_nums:  # Process all 23 chapters
    ch_id = f"ch_{ch_num:02d}"
    cards_dir = os.path.join(OUT_DIR, 'chapters', ch_id, 'cards')

    # Skip if already processed (cards exist)
    if os.path.isdir(cards_dir) and len(os.listdir(cards_dir)) > 10:
        existing = len([f for f in os.listdir(cards_dir) if f.endswith('.json')])
        print(f"  {ch_id}: SKIP ({existing} cards already exist)")
        continue

    m = chapter_texts[ch_num]
    ch_start = m.start()
    next_start = None
    for n in sorted(chapter_texts.keys()):
        if n > ch_num and n in chapter_texts:
            nm = chapter_texts[n]
            if nm.start() > ch_start:
                next_start = nm.start()
                break
    if next_start is None:
        ch_text = full_text[ch_start:]
    else:
        ch_text = full_text[ch_start:next_start]

    ch_text = ch_text.strip()
    print(f"\n{'='*60}")
    print(f"  {ch_id}: {len(ch_text)} chars")
    print(f"{'='*60}")

    try:
        t0 = time.time()
        result = call_claude(ch_text)
        dt = time.time() - t0

        # Extract JSON array from response
        content = result.get("content", [{}])[0].get("text", "")
        # Find JSON array in the response
        json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if json_match:
            cards = json.loads(json_match.group(0))
            print(f"  Got {len(cards)} cards in {dt:.0f}s")

            # Write cards
            cards_dir = os.path.join(OUT_DIR, 'chapters', ch_id, 'cards')
            os.makedirs(cards_dir, exist_ok=True)

            for card in cards:
                # Extract md_content and remove from JSON
                md_content = card.pop("md_content", "")
                point_id = card["point_id"]
                section_id = card.get("section_id", "sec_01")
                file_stem = f"{ch_id}_{section_id}_{point_id}"

                card["content_file"] = f"{file_stem}.md"
                card["content_md_path"] = f"subjects/high_itpmp/chapters/{ch_id}/cards/{file_stem}.md"

                with open(os.path.join(cards_dir, f"{file_stem}.json"), 'w', encoding='utf-8') as f:
                    json.dump(card, f, ensure_ascii=False, indent=2)
                with open(os.path.join(cards_dir, f"{file_stem}.md"), 'w', encoding='utf-8') as f:
                    f.write(md_content)

            print(f"  Saved to {cards_dir}")
        else:
            print(f"  ERROR: No JSON array found in response")
            print(f"  Response preview: {content[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")
