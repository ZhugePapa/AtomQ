#!/usr/bin/env python3
"""
Full OCR pipeline for 2026高项三色笔记 PDF.
Phase 1: Quick scan → chapter boundaries
Phase 2: Per-chapter deep OCR → knowledge cards with red text detection
Output: data-deepseek/content_package/public/ following conventions
"""
import subprocess, os, json, re, struct, shutil, time
from xml.etree import ElementTree as ET
from datetime import datetime

PDF = "/Users/leiwang/Downloads/三色笔记/2026新版高项三色笔记（信息系统项目管理师）.pdf"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'pipeline_output')
CONTENT_OUT = os.path.join(ROOT, 'content_package', 'public', 'subjects', 'high_itpmp')
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(CONTENT_OUT, 'chapters'), exist_ok=True)
os.makedirs(os.path.join(CONTENT_OUT, 'questions'), exist_ok=True)

NOW = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')
DPI = 200

# ── Chapter definitions (from manifest.json) ──
CHAPTERS = [
    ("ch_01", "信息化发展", 25),
    ("ch_02", "信息技术发展", 34),
    ("ch_03", "信息系统治理", 17),
    ("ch_04", "信息系统管理", 28),
    ("ch_05", "信息系统工程", 59),
    ("ch_06", "项目管理概论", 30),
    ("ch_07", "立项管理", 9),
    ("ch_08", "整合管理", 31),
    ("ch_09", "范围管理", 27),
    ("ch_10", "进度管理", 30),
    ("ch_11", "成本管理", 19),
    ("ch_12", "质量管理", 29),
    ("ch_13", "资源管理", 38),
    ("ch_14", "沟通管理", 18),
    ("ch_15", "风险管理", 35),
    ("ch_16", "采购管理", 25),
    ("ch_17", "干系人管理", 19),
    ("ch_18", "项目绩效域", 50),
    ("ch_19", "配置与变更管理", 21),
    ("ch_20", "高级项目管理", 19),
    ("ch_21", "项目管理科学基础", 2),
    ("ch_22", "组织通用治理", 20),
    ("ch_23", "组织通用管理", 35),
]

# ── Utility: pdftoppm single page ──
def page_to_png(page_num, dpi=DPI):
    """Convert one PDF page to PNG. Returns path."""
    prefix = os.path.join(OUT, f'pg_{page_num:04d}')
    subprocess.run([
        'pdftoppm', '-png', '-r', str(dpi),
        '-f', str(page_num), '-l', str(page_num),
        PDF, prefix
    ], check=True, capture_output=True)
    # Find the actual file (pdftoppm adds suffix like -001)
    for f in sorted(os.listdir(OUT)):
        if f.startswith(f'pg_{page_num:04d}') and f.endswith('.png'):
            return os.path.join(OUT, f)
    return None

def ocr_page(png_path, lang='chi_sim', psm=6, hocr=False):
    """OCR a page image. Returns (text, hocr_path or None)."""
    base = png_path.rsplit('.', 1)[0] + '_ocr'
    args = ['tesseract', png_path, base, '-l', lang, '--psm', str(psm)]
    if hocr:
        args.append('hocr')
    subprocess.run(args, check=True, capture_output=True, timeout=60)
    if hocr:
        return None, base + '.hocr'
    else:
        with open(base + '.txt', 'r', encoding='utf-8') as f:
            return f.read(), None

def page_to_ppm(page_num, dpi=DPI):
    """Convert one PDF page to PPM for pixel analysis."""
    prefix = os.path.join(OUT, f'ppm_{page_num:04d}')
    subprocess.run([
        'pdftoppm', '-r', str(dpi),
        '-f', str(page_num), '-l', str(page_num),
        PDF, prefix
    ], check=True, capture_output=True)
    for f in sorted(os.listdir(OUT)):
        if f.startswith(f'ppm_{page_num:04d}') and f.endswith('.ppm'):
            return os.path.join(OUT, f)
    return None

def load_ppm_pixels(ppm_path):
    """Load PPM file, return (pixels_bytes, width, height)."""
    with open(ppm_path, 'rb') as f:
        magic = f.readline().strip()
        line = f.readline()
        while line.startswith(b'#'): line = f.readline()
        w, h = map(int, line.split())
        maxval = int(f.readline().strip())
        px = f.read()
    return px, w, h

def get_pixel(px, w, x, y):
    idx = (y * w + x) * 3
    return px[idx], px[idx+1], px[idx+2]

def is_red(r, g, b):
    if r < 60: return False
    if g == 0: g = 1
    if b == 0: b = 1
    return (r / g > 1.25 and r / b > 1.25)

def detect_red_phrases(hocr_path, ppm_px, ppm_w, ppm_h):
    """Parse hOCR, detect red words, merge into phrases."""
    ns = {'x': 'http://www.w3.org/1999/xhtml'}
    tree = ET.parse(hocr_path)
    root = tree.getroot()

    words = []
    for span in root.findall('.//x:span[@class="ocrx_word"]', ns):
        title = span.get('title', '')
        text = (span.text or '').strip()
        if not text: continue
        bm = re.search(r'bbox\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', title)
        if not bm: continue
        x0, y0, x1, y1 = [int(b) for b in bm.groups()]
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(ppm_w, x1), min(ppm_h, y1)

        red, total = 0, 0
        step = max(1, min(x1-x0, y1-y0) // 3)
        for y in range(y0, y1, step):
            for x in range(x0, x1, step):
                try:
                    r, g, b = get_pixel(ppm_px, ppm_w, x, y)
                    if is_red(r, g, b): red += 1
                    total += 1
                except: pass

        is_w_red = total > 3 and red / total > 0.2
        words.append({'text': text, 'is_red': is_w_red, 'x0': x0, 'y0': y0})

    # Merge adjacent red words on same line
    phrases = []
    i = 0
    while i < len(words):
        if words[i]['is_red']:
            phrase = words[i]['text']
            j = i + 1
            while j < len(words) and words[j]['is_red'] and abs(words[j]['y0'] - words[i]['y0']) < 25:
                phrase += words[j]['text']
                j += 1
            if len(phrase) >= 2:
                phrases.append(phrase)
            i = j
        else:
            i += 1

    # Filter noise: remove very common single chars, punctuation
    noise = {'的', '了', '是', '在', '和', '与', '、', '。', '，', '：', '“', '”', '（', '）'}
    phrases = [p for p in phrases if p not in noise and len(p) >= 2]

    # Deduplicate while preserving order
    seen = set()
    result = []
    for p in phrases:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


# ═══════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Process only first 3 chapters for now (test run)
    # Change to CHAPTERS for full run
    TARGET_CHAPTERS = CHAPTERS[:3]  # Chapters 1-3

    all_cards = []

    for ch_id, ch_title, card_count in TARGET_CHAPTERS:
        print(f"\n{'='*60}")
        print(f"  {ch_id}: {ch_title} (target: {card_count} cards)")
        print(f"{'='*60}")

        # Estimate page range from card count (~4 pages per card)
        ch_idx = int(ch_id.split('_')[1])
        # Simple heuristic: chapters start at roughly cumulative pages
        # For now, process a fixed page range per chapter
        # We'll refine after the quick scan finds actual boundaries

        # Find chapter start page by scanning
        search_start = max(1, (ch_idx - 1) * 25)  # rough estimate
        search_end = min(2594, search_start + 100)

        ch_start_page = None
        for pg in range(search_start, search_end, 5):  # Sample every 5th page
            png = page_to_png(pg, dpi=100)  # Low res for speed
            if not png: continue
            text, _ = ocr_page(png, psm=6)
            if text and f'第{ch_idx}章' in text.replace(' ', ''):
                ch_start_page = pg
                print(f"  Found chapter start at page {pg}")
                os.remove(png)
                # Clean up OCR files
                for f in os.listdir(OUT):
                    if 'ocr' in f:
                        os.remove(os.path.join(OUT, f))
                break
            if png and os.path.exists(png):
                os.remove(png)

        if not ch_start_page:
            print(f"  WARNING: Chapter start not found, using estimate")
            ch_start_page = search_start

        # Estimate end page (4 pages per card)
        ch_end_page = min(2594, ch_start_page + card_count * 4 + 10)

        print(f"  Processing pages {ch_start_page}-{ch_end_page}")

        # Process each page with full OCR + red detection
        ch_text_parts = []
        for pg in range(ch_start_page, ch_end_page + 1):
            t0 = time.time()

            # PNG for OCR
            png = page_to_png(pg, dpi=DPI)
            if not png: continue

            # OCR with hOCR (for word positions)
            _, hocr = ocr_page(png, hocr=True)
            # Plain text
            text, _ = ocr_page(png, psm=6)

            # Red detection
            ppm = page_to_ppm(pg, dpi=DPI)
            red_phrases = []
            if ppm and hocr:
                px, pw, ph = load_ppm_pixels(ppm)
                red_phrases = detect_red_phrases(hocr, px, pw, ph)

            # Apply red highlighting to text
            if red_phrases and text:
                for phrase in sorted(red_phrases, key=len, reverse=True):
                    if len(phrase) >= 2 and phrase in text:
                        text = text.replace(phrase, f'=={phrase}==')

            ch_text_parts.append(text or '')

            # Cleanup
            for f in [png, ppm, hocr]:
                if f and os.path.exists(f):
                    os.remove(f)
            # Clean OCR output files
            for f in os.listdir(OUT):
                if '_ocr' in f or f.endswith('.hocr'):
                    os.remove(os.path.join(OUT, f))

            dt = time.time() - t0
            if pg % 10 == 0:
                print(f"  Page {pg}: {len(text or '')} chars, {len(red_phrases)} red phrases ({dt:.1f}s)")

        # Join all page text for this chapter
        full_chapter_text = '\n'.join(ch_text_parts)
        ch_text_path = os.path.join(OUT, f'{ch_id}_full_text.txt')
        with open(ch_text_path, 'w', encoding='utf-8') as f:
            f.write(full_chapter_text)

        print(f"  Chapter {ch_id}: {len(full_chapter_text)} total chars")
        print(f"  Saved: {ch_text_path}")

    print(f"\n{'='*60}")
    print(f"  Pipeline complete!")
    print(f"  Output: {OUT}")
