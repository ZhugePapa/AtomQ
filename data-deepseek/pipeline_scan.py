#!/usr/bin/env python3
"""Phase 1: Quick scan all 2594 pages to find chapter/section boundaries."""
import subprocess, os, json, re

PDF = "/Users/leiwang/Downloads/三色笔记/2026新版高项三色笔记（信息系统项目管理师）.pdf"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline_output')
os.makedirs(OUT, exist_ok=True)

TOTAL_PAGES = 2594
BATCH = 50
STATE_FILE = os.path.join(OUT, 'scan_state.json')

# Resume from last checkpoint
start_page = 1
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        state = json.load(f)
        start_page = state.get('last_page', 0) + 1
        print(f"Resuming from page {start_page}")

chapter_boundaries = []
if os.path.exists(STATE_FILE):
    chapter_boundaries = state.get('chapters', [])

for batch_start in range(start_page, TOTAL_PAGES + 1, BATCH):
    batch_end = min(batch_start + BATCH - 1, TOTAL_PAGES)

    # Convert batch to images at low res (150 DPI, fast)
    prefix = os.path.join(OUT, f'batch_{batch_start:04d}')
    subprocess.run([
        'pdftoppm', '-png', '-r', '100',  # Low res for speed
        '-f', str(batch_start), '-l', str(batch_end),
        PDF, prefix
    ], check=True, capture_output=True)

    # OCR each page in batch
    for pg in range(batch_start, batch_end + 1):
        # Find the actual PNG file (pdftoppm adds offset suffix)
        png_file = None
        for f in sorted(os.listdir(OUT)):
            if f.startswith(f'batch_{batch_start:04d}') and f.endswith('.png'):
                # Parse page number from pdftoppm naming
                png_file = os.path.join(OUT, f)
                break

        if not png_file:
            continue

        # Quick OCR (just text, no hOCR)
        txt_prefix = os.path.join(OUT, f'txt_{pg:04d}')
        subprocess.run([
            'tesseract', png_file, txt_prefix,
            '-l', 'chi_sim', '--psm', '6'
        ], check=True, capture_output=True, timeout=30)

        txt_file = txt_prefix + '.txt'
        if os.path.exists(txt_file):
            with open(txt_file, 'r', encoding='utf-8') as f:
                text = f.read()

            # Check for chapter/section markers
            ch_match = re.search(r'第\s*(\d+)\s*章', text)
            sec_match = re.search(r'(\d+\.\d+)', text)

            if ch_match:
                ch_num = int(ch_match.group(1))
                ch_title = text[ch_match.end():ch_match.end()+30].strip()
                existing = [c for c in chapter_boundaries if c['chapter'] == ch_num]
                if not existing:
                    chapter_boundaries.append({
                        'chapter': ch_num,
                        'start_page': pg,
                        'title_hint': ch_title
                    })
                    print(f"  Ch {ch_num:2d} @ page {pg}: {ch_title}")

            # Clean up OCR text file
            os.remove(txt_file)

    # Clean up batch images
    for f in os.listdir(OUT):
        if f.startswith(f'batch_{batch_start:04d}') and f.endswith('.png'):
            os.remove(os.path.join(OUT, f))

    # Save state
    state = {
        'last_page': batch_end,
        'chapters': chapter_boundaries,
        'total_pages': TOTAL_PAGES
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    progress = batch_end / TOTAL_PAGES * 100
    print(f"  Progress: {batch_end}/{TOTAL_PAGES} ({progress:.1f}%) | Chapters found: {len(chapter_boundaries)}")

# Finalize
chapter_boundaries.sort(key=lambda x: x['chapter'])
print(f"\n=== Chapter boundaries ===")
for ch in chapter_boundaries:
    print(f"  Chapter {ch['chapter']:2d}: page {ch['start_page']:4d} - {ch['title_hint'][:40]}")

with open(os.path.join(OUT, 'chapter_map.json'), 'w') as f:
    json.dump(chapter_boundaries, f, ensure_ascii=False, indent=2)
print(f"\nSaved: {os.path.join(OUT, 'chapter_map.json')}")
print(f"Total chapters found: {len(chapter_boundaries)}")
