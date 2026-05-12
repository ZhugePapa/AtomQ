#!/usr/bin/env python3
"""
Simplified OCR pipeline:
  1. Batch-convert PDF pages to images (pdftoppm)
  2. OCR each image (tesseract)
  3. Assemble full text, detect chapter boundaries
  4. Split into chapters, save raw text
"""
import subprocess, os, json, re, time, glob

PDF = "/Users/leiwang/Downloads/三色笔记/2026新版高项三色笔记（信息系统项目管理师）.pdf"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'ocr_output')
os.makedirs(OUT, exist_ok=True)

BATCH = 10   # Pages per batch
DPI = 150    # Resolution (150 = good balance of speed/quality)
START = 1
END = 229    # Actual PDF page count

# Resume support
CHECKPOINT = os.path.join(OUT, 'checkpoint.json')
all_text = []
start_batch = START

if os.path.exists(CHECKPOINT):
    with open(CHECKPOINT) as f:
        cp = json.load(f)
        all_text = cp.get('text_pages', [])
        start_batch = cp.get('last_batch_end', START - 1) + 1
        print(f"Resuming from page {start_batch} ({len(all_text)} pages already processed)")

print(f"PDF: {PDF}")
print(f"DPI: {DPI}, Batch: {BATCH}, Pages: {start_batch}-{END}")
print(f"Output: {OUT}\n")

t0_total = time.time()

for batch_start in range(start_batch, END + 1, BATCH):
    batch_end = min(batch_start + BATCH - 1, END)
    t0 = time.time()

    # Step 1: Convert batch to PNG
    prefix = os.path.join(OUT, f'b{batch_start:04d}')
    subprocess.run([
        'pdftoppm', '-png', '-r', str(DPI),
        '-f', str(batch_start), '-l', str(batch_end),
        PDF, prefix
    ], check=True, capture_output=True)

    # Step 2: OCR each PNG
    pngs = sorted(glob.glob(os.path.join(OUT, f'b{batch_start:04d}*.png')))
    for png in pngs:
        # Extract page number from filename (b0001-01.png → page batch_start+0)
        base = os.path.splitext(png)[0]
        txt_out = base + '_txt'

        try:
            subprocess.run([
                'tesseract', png, txt_out,
                '-l', 'chi_sim', '--psm', '6'
            ], check=True, capture_output=True, timeout=30)
        except:
            continue

        txt_file = txt_out + '.txt'
        if os.path.exists(txt_file):
            with open(txt_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            if text:
                all_text.append(text)
            os.remove(txt_file)

        # Delete PNG to save space
        os.remove(png)

    dt = time.time() - t0
    progress = batch_end / END * 100
    print(f"  Batch {batch_start}-{batch_end}: {dt:.1f}s | Total pages: {len(all_text)} | Progress: {progress:.0f}%")

    # Save checkpoint
    with open(CHECKPOINT, 'w') as f:
        json.dump({'last_batch_end': batch_end, 'text_pages': all_text}, f)

# Step 3: Assemble full text
full_text = '\n\n--- PAGE BREAK ---\n\n'.join(all_text)
text_path = os.path.join(OUT, 'full_text.txt')
with open(text_path, 'w', encoding='utf-8') as f:
    f.write(full_text)

dt_total = time.time() - t0_total
print(f"\n{'='*60}")
print(f"Complete! {len(all_text)} pages in {dt_total:.0f}s")
print(f"Total chars: {len(full_text)}")
print(f"Saved: {text_path}")

# Step 4: Detect chapter boundaries
print(f"\n=== Chapter detection ===")
for ch_num in range(1, 25):
    pattern = f'第{ch_num}章' if ch_num < 10 else f'第{ch_num:02d}章'
    idx = full_text.find(pattern)
    if idx >= 0:
        ctx = full_text[max(0,idx-5):idx+40].replace('\n',' ')
        print(f"  Chapter {ch_num:2d}: found at char {idx} → '{ctx}'")
    else:
        # Try OCR variants
        for variant in [f'第 {ch_num} 章', f'第{ch_num:02d} 章']:
            idx = full_text.find(variant)
            if idx >= 0:
                print(f"  Chapter {ch_num:2d}: variant at char {idx}")
                break
        else:
            print(f"  Chapter {ch_num:2d}: NOT FOUND")
