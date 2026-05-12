#!/usr/bin/env python3
"""Extract first page image from PDF and OCR it with tesseract."""
import re, zlib, subprocess, os, sys

fp = "/Users/leiwang/Downloads/三色笔记/2026新版高项三色笔记（信息系统项目管理师）.pdf"
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ocr_output')
os.makedirs(out_dir, exist_ok=True)

with open(fp, 'rb') as f:
    data = f.read()

# Find page objects and their contents
obj_pat = re.compile(rb'(\d+ \d+ obj.*?endobj)', re.DOTALL)

# Find first page object
page_found = 0
for m in obj_pat.finditer(data):
    obj = m.group(1)
    if b'/Type /Page' not in obj and b'/Type/Page' not in obj:
        continue

    page_found += 1
    if page_found > 3:  # Only first 3 pages
        break

    oid = re.match(rb'(\d+ \d+ obj)', obj).group(1).decode()
    print(f"\n=== Page {page_found} (obj {oid}) ===")

    # Get content stream reference
    cont = re.search(rb'/Contents\s+(\d+ \d+ R)', obj)
    if not cont:
        # Check for array of content streams: /Contents [1 0 R 2 0 R]
        cont_arr = re.search(rb'/Contents\s*\[(.*?)\]', obj, re.DOTALL)
        if cont_arr:
            refs = re.findall(rb'(\d+ \d+ R)', cont_arr.group(1))
            print(f"  Content array: {[r.decode() for r in refs]}")
        else:
            print(f"  No /Contents found")
            # Show raw page object for debugging
            print(f"  Raw: {obj[:500]}")
        continue

    ref = cont.group(1).decode()
    print(f"  Content ref: {ref}")

    # Find the content stream object
    parts = ref.split()
    prefix = f'{parts[0]} {parts[1]} obj'.encode()
    idx = data.find(prefix)
    if idx < 0:
        print(f"  Content object not found!")
        continue

    end = data.find(b'endobj', idx)
    stream_obj = data[idx:end+6] if end >= 0 else data[idx:idx+10000]

    # Extract and decompress stream
    sm = re.search(rb'stream\r?\n(.*?)endstream', stream_obj, re.DOTALL)
    if not sm:
        print(f"  No stream in content object")
        continue

    raw = sm.group(1)
    if b'/FlateDecode' in stream_obj:
        try:
            raw = zlib.decompress(raw)
        except:
            print(f"  FlateDecode failed")
            continue

    # Look for inline images (BI/ID/EI) or Do operators referencing XObjects
    do_refs = re.findall(rb'/(\S+)\s+Do', raw)
    if do_refs:
        print(f"  XObject Do refs: {[d.decode() for d in do_refs[:5]]}")

    # Check for inline images
    if b'BI' in raw and b'ID' in raw:
        print(f"  Has inline images")

    # Show first 300 bytes of content stream
    print(f"  Stream preview: {raw[:300]}")

print("\n=== Image extraction test ===")
# Find all image streams with DCTDecode (JPEG)
img_count = 0
for m in obj_pat.finditer(data):
    obj = m.group(1)
    if b'/DCTDecode' not in obj or b'stream' not in obj:
        continue

    sm = re.search(rb'stream\r?\n(.*?)endstream', obj, re.DOTALL)
    if not sm:
        continue

    raw = sm.group(1)
    # JPEG starts with FF D8
    if raw[:2] == b'\xff\xd8':
        img_count += 1
        if img_count <= 3:
            path = os.path.join(out_dir, f'page_{img_count:03d}.jpg')
            with open(path, 'wb') as f:
                f.write(raw)
            print(f"  Saved: {path} ({len(raw)} bytes)")

            # Run OCR
            try:
                result = subprocess.run(
                    ['tesseract', path, 'stdout', '-l', 'chi_sim', '--psm', '6'],
                    capture_output=True, text=True, timeout=60
                )
                text = result.stdout.strip()
                print(f"  OCR result ({len(text)} chars): {text[:200]}")
            except Exception as e:
                print(f"  OCR error: {e}")

print(f"\nTotal JPEG images found: {img_count}")
