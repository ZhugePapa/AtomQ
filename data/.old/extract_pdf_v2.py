#!/usr/bin/env python3
"""Complete PDF text extractor with CMap support for Chinese PDFs."""
import re, zlib, sys, os

def find_obj(data, obj_num, obj_gen=0):
    """Find a specific object by number and generation."""
    prefix = f'{obj_num} {obj_gen} obj'.encode()
    idx = data.find(prefix)
    if idx < 0:
        return None
    end = data.find(b'endobj', idx)
    if end < 0:
        return data[idx:idx+5000]
    return data[idx:end+6]

def get_stream(obj):
    """Extract and decompress stream from an object."""
    sm = re.search(rb'stream\r?\n(.*?)endstream', obj, re.DOTALL)
    if not sm:
        return None
    raw = sm.group(1).rstrip()
    if b'/FlateDecode' in obj:
        try:
            return zlib.decompress(raw)
        except:
            return raw
    return raw

def parse_cmap(stream_data):
    """Parse a CMap stream and return dict mapping hex codes to Unicode chars."""
    text = stream_data.decode('latin-1', errors='replace')
    mapping = {}

    # parse bfrange: <start> <end> <unicode_start>
    bfranges = re.findall(
        r'(\d+) beginbfrange\s*(.*?)\s*endbfrange', text, re.DOTALL)
    for _, ranges in bfranges:
        entries = re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', ranges)
        for start_hex, end_hex, uni_hex in entries:
            start = int(start_hex, 16)
            end = int(end_hex, 16)
            uni = int(uni_hex, 16)
            for i in range(end - start + 1):
                mapping[f'{start+i:04X}'] = chr(uni + i)

    # parse bfchar: <code> <unicode>
    bfchars = re.findall(
        r'(\d+) beginbfchar\s*(.*?)\s*endbfchar', text, re.DOTALL)
    for _, chars in bfchars:
        entries = re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', chars)
        for code_hex, uni_hex in entries:
            mapping[code_hex.upper()] = chr(int(uni_hex, 16))

    return mapping

def build_font_map(data):
    """Build complete glyph-to-Unicode mapping from all fonts."""
    glyph_map = {}

    # Find all objects
    obj_pattern = re.compile(rb'(\d+ \d+ obj.*?endobj)', re.DOTALL)
    for m in obj_pattern.finditer(data):
        obj = m.group(1)
        if b'/Type /Font' not in obj and b'/Subtype /Type0' not in obj:
            continue

        # Get font name
        fn_match = re.search(rb'/BaseFont\s*/([^\s/]+)', obj)
        if not fn_match:
            continue
        font_name = fn_match.group(1).decode()

        # Get ToUnicode reference
        tu_match = re.search(rb'/ToUnicode\s+(\d+ \d+ R)', obj)
        if not tu_match:
            continue

        # Follow the reference to get the CMap stream
        tu_ref = tu_match.group(1).decode()
        parts = tu_ref.split()
        cmap_obj = find_obj(data, int(parts[0]), int(parts[1]))
        if not cmap_obj:
            continue

        cmap_stream = get_stream(cmap_obj)
        if not cmap_stream:
            continue

        mapping = parse_cmap(cmap_stream)
        if mapping:
            glyph_map[font_name] = mapping
            print(f"  Font {font_name}: {len(mapping)} glyphs mapped")

    return glyph_map

def extract_text_with_map(data, glyph_map):
    """Extract text from all pages using font-specific glyph maps."""
    all_lines = []

    # Find page objects and their contents
    obj_pattern = re.compile(rb'(\d+ \d+ obj.*?endobj)', re.DOTALL)

    # First pass: build page -> content stream mapping
    page_objects = []
    stream_cache = {}

    for m in obj_pattern.finditer(data):
        obj = m.group(1)
        if b'/Type /Page' in obj or b'/Type/Page' in obj:
            # Get the content stream reference
            cont_match = re.search(rb'/Contents\s+(\d+ \d+ R)', obj)
            if cont_match:
                page_objects.append(cont_match.group(1).decode())

    # Process page content streams in order
    seen = set()
    for ref in page_objects:
        if ref in seen:
            continue
        seen.add(ref)

        parts = ref.split()
        stream_obj = find_obj(data, int(parts[0]), int(parts[1]))
        if not stream_obj:
            continue

        stream_data = get_stream(stream_obj)
        if not stream_data:
            continue

        # Extract text blocks
        bt_blocks = re.findall(rb'BT(.*?)ET', stream_data, re.DOTALL)
        page_lines = []

        for bt in bt_blocks:
            # Get current font
            font_match = re.search(rb'/(C\d+)\s+', bt)
            font_name = font_match.group(1).decode() if font_match else None

            # Get hex text from Tj
            tj_match = re.search(rb'<([0-9A-Fa-f]+)>\s*Tj', bt)
            if not tj_match:
                continue

            hex_str = tj_match.group(1)
            # Split into 4-char hex codes (CID font glyph indices)
            glyphs = [hex_str[i:i+4] for i in range(0, len(hex_str), 4)]

            text = ''
            font_map = glyph_map.get(font_name, {})
            for g in glyphs:
                text += font_map.get(g, f'[{g}]')

            if text.strip():
                page_lines.append(text)

        if page_lines:
            all_lines.append(''.join(page_lines))

    return '\n'.join(all_lines)

if __name__ == '__main__':
    fp = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        '~/Downloads/三色笔记/拆分/2026新版高项三色笔记（信息系统项目管理师）（拖移项目 01）.pdf')

    with open(fp, 'rb') as f:
        data = f.read()

    print("Building font glyph map...")
    glyph_map = build_font_map(data)

    print(f"\nTotal fonts with CMap: {len(glyph_map)}")
    print("Extracting text...")

    text = extract_text_with_map(data, glyph_map)

    out = sys.argv[2] if len(sys.argv) > 2 else fp.replace('.pdf', '_extracted.txt')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"Saved to: {out}")
    print(f"\nFirst 300 chars:\n{text[:300]}")
