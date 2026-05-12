#!/usr/bin/env python3
"""Test: PDF page → PPM image → OCR hOCR → red text detection (stdlib only)."""
import subprocess, os, re, struct
from xml.etree import ElementTree as ET

PDF = "/Users/leiwang/Downloads/三色笔记/2026新版高项三色笔记（信息系统项目管理师）.pdf"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_output')
os.makedirs(OUT, exist_ok=True)
PAGE = 1

# ── Step 1: Convert PDF to PPM (plain format, stdlib parseable) ──
prefix = os.path.join(OUT, f'page_{PAGE:04d}')
subprocess.run([
    'pdftoppm', '-r', '200', '-f', str(PAGE), '-l', str(PAGE),
    PDF, prefix
], check=True)

# pdftoppm adds -1, -2 etc for multi-page; find the actual file
ppm_path = None
for f in os.listdir(OUT):
    if f.startswith(f'page_{PAGE:04d}') and (f.endswith('.ppm') or f.endswith('.pnm')):
        ppm_path = os.path.join(OUT, f)
        break
if not ppm_path:
    raise FileNotFoundError(f"No PPM file found for page {PAGE}")

size_kb = os.path.getsize(ppm_path) / 1024
print(f"[1] PPM saved: {ppm_path} ({size_kb:.0f}KB)")

# ── Step 2: Parse PPM header and get pixel data ──
with open(ppm_path, 'rb') as f:
    magic = f.readline().strip()
    if magic not in (b'P6', b'P5'):
        raise ValueError(f"Unsupported PPM format: {magic}")
    # Skip comments
    line = f.readline()
    while line.startswith(b'#'):
        line = f.readline()
    width, height = map(int, line.split())
    maxval = int(f.readline().strip())
    pixel_data = f.read()

bytes_per_pixel = 3 if magic == b'P6' else 1
expected = width * height * bytes_per_pixel
if len(pixel_data) < expected:
    pixel_data += f.read(expected - len(pixel_data))

print(f"[2] Image: {width}x{height}, maxval={maxval}, {len(pixel_data)} bytes")

def get_pixel(x, y):
    """Get (R,G,B) at pixel position."""
    idx = (y * width + x) * 3
    return pixel_data[idx], pixel_data[idx+1], pixel_data[idx+2]

def is_red(r, g, b):
    """Detect red text: R dominates over G and B."""
    if r < 80:  # Too dark
        return False
    if r > g * 1.3 and r > b * 1.3:
        return True
    # Also detect reddish-orange (三色笔记 uses a warm red)
    if r > g * 1.15 and r > b * 1.5 and r > 120:
        return True
    return False

# ── Step 3: OCR with tesseract hOCR ──
# tesseract needs PNG for OCR, so convert a small PNG from PPM
png_path = prefix + '.png'
subprocess.run([
    'pdftoppm', '-png', '-r', '200', '-f', str(PAGE), '-l', str(PAGE),
    PDF, prefix
], check=True)
for f in os.listdir(OUT):
    if f.startswith(f'page_{PAGE:04d}') and f.endswith('.png'):
        png_path = os.path.join(OUT, f)
        break

hocr_prefix = os.path.join(OUT, f'hocr_{PAGE:04d}')
subprocess.run([
    'tesseract', png_path, hocr_prefix, '-l', 'chi_sim', '--psm', '6', 'hocr'
], check=True)
hocr_file = hocr_prefix + '.hocr'
print(f"[3] hOCR saved: {hocr_file}")

# ── Step 4: Parse hOCR and detect red words ──
ns = {'x': 'http://www.w3.org/1999/xhtml'}
tree = ET.parse(hocr_file)
root = tree.getroot()

all_words = []
red_words = []

for span in root.findall('.//x:span[@class="ocrx_word"]', ns):
    title = span.get('title', '')
    text = (span.text or '').strip()
    if not text:
        continue

    bbox_match = re.search(r'bbox\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', title)
    if not bbox_match:
        continue

    x0, y0, x1, y1 = [int(b) for b in bbox_match.groups()]
    # Scale bbox to match PPM resolution (tesseract might use different DPI)
    # pdftoppm -r 200 → tesseract uses image pixels directly
    # But tesseract may rescale. For now assume same resolution.

    # Clamp to image bounds
    x0 = max(0, min(x0, width - 1))
    y0 = max(0, min(y0, height - 1))
    x1 = max(x0 + 1, min(x1, width))
    y1 = max(y0 + 1, min(y1, height))

    # Sample pixels in bbox
    red_count = 0
    total = 0
    sample_step = max(1, min(y1 - y0, x1 - x0) // 4)
    for y in range(y0, y1, sample_step):
        for x in range(x0, x1, sample_step):
            try:
                r, g, b = get_pixel(x, y)
                if is_red(r, g, b):
                    red_count += 1
                total += 1
            except IndexError:
                pass

    word_info = {'text': text, 'bbox': [x0, y0, x1, y1]}
    all_words.append(word_info)

    if total > 4 and red_count / total > 0.25:
        word_info['red_ratio'] = round(red_count / total, 2)
        red_words.append(word_info)

print(f"[4] Total words: {len(all_words)}, Red words: {len(red_words)}")
for w in red_words[:20]:
    print(f"    RED({w.get('red_ratio','?')}): '{w['text']}'")
print(f"    ...")
for w in all_words[10:20]:
    is_r = w in red_words
    print(f"    {'RED' if is_r else '   '}: '{w['text']}'")

print(f"\nDone! Output: {OUT}")
