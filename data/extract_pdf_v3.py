#!/usr/bin/env python3
"""Complete PDF text extractor v3 — short font name mapping + writable output."""
import re, zlib, sys, os

def get_stream(obj):
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
    text = stream_data.decode('latin-1', errors='replace')
    mapping = {}
    bfranges = re.findall(r'(\d+) beginbfrange\s*(.*?)\s*endbfrange', text, re.DOTALL)
    for _, ranges in bfranges:
        entries = re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', ranges)
        for start_hex, end_hex, uni_hex in entries:
            start, end, uni = int(start_hex, 16), int(end_hex, 16), int(uni_hex, 16)
            for i in range(end - start + 1):
                mapping[f'{start+i:04X}'] = chr(uni + i)
    bfchars = re.findall(r'(\d+) beginbfchar\s*(.*?)\s*endbfchar', text, re.DOTALL)
    for _, chars in bfchars:
        entries = re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', chars)
        for code_hex, uni_hex in entries:
            mapping[code_hex.upper()] = chr(int(uni_hex, 16))
    return mapping

def build_all_maps(data):
    """Build short-font-name → glyph map AND font-name registry."""
    obj_pattern = re.compile(rb'(\d+ \d+ obj.*?endobj)', re.DOTALL)

    # Step 1: Map font object number → BaseFont name
    obj_to_font = {}
    for m in obj_pattern.finditer(data):
        obj = m.group(1)
        oid = re.match(rb'(\d+ \d+ obj)', obj).group(1).decode()
        if b'/Type /Font' in obj and b'/BaseFont' in obj:
            fn = re.search(rb'/BaseFont\s*/([^\s/>]+)', obj)
            if fn:
                obj_to_font[oid] = fn.group(1).decode()

    # Step 2: Build glyph map per BaseFont
    glyph_map = {}
    for m in obj_pattern.finditer(data):
        obj = m.group(1)
        if b'/Type /Font' not in obj or b'/BaseFont' not in obj:
            continue
        fn_match = re.search(rb'/BaseFont\s*/([^\s/>]+)', obj)
        font_name = fn_match.group(1).decode()
        tu_match = re.search(rb'/ToUnicode\s+(\d+ \d+ R)', obj)
        if not tu_match:
            continue
        cmap_obj = None
        tu_ref = tu_match.group(1).decode()
        parts = tu_ref.split()
        prefix = f'{parts[0]} {parts[1]} obj'.encode()
        idx = data.find(prefix)
        if idx >= 0:
            end = data.find(b'endobj', idx)
            cmap_obj = data[idx:end+6] if end >= 0 else data[idx:idx+5000]
        if not cmap_obj:
            continue
        cmap_stream = get_stream(cmap_obj)
        if not cmap_stream:
            continue
        mapping = parse_cmap(cmap_stream)
        if mapping:
            glyph_map[font_name] = mapping

    # Step 3: Map page content font names (/C1, /C2...) → BaseFont names
    # Font resources are in page resource dictionaries
    font_name_map = {}  # C1 → AAAAAB+MicrosoftYaHei

    for m in obj_pattern.finditer(data):
        obj = m.group(1)
        # Look for font resource dictionaries
        if b'/Font' in obj and b'/' in obj:
            # Find /C1 ... /CN → obj ref mappings
            font_entries = re.findall(rb'/(C\d+)\s+(\d+ \d+ R)', obj)
            for short_name, ref in font_entries:
                short = short_name.decode()
                ref_str = ref.decode()
                if ref_str in obj_to_font:
                    font_name_map[short] = obj_to_font[ref_str]

    print(f"Font name mappings (short→full): {len(font_name_map)}")
    for k, v in sorted(font_name_map.items(), key=lambda x: int(x[0][1:]))[:10]:
        print(f"  {k} → {v[:50]}")
    if len(font_name_map) > 10:
        print(f"  ... and {len(font_name_map)-10} more")

    return glyph_map, font_name_map

def extract_all_text(data, glyph_map, font_name_map):
    """Extract text from all page content streams."""
    all_pages = []
    obj_pattern = re.compile(rb'(\d+ \d+ obj.*?endobj)', re.DOTALL)

    # Find content streams that have lots of BT blocks (pages)
    for m in obj_pattern.finditer(data):
        obj = m.group(1)
        stream_data = get_stream(obj)
        if not stream_data:
            continue

        bt_blocks = re.findall(rb'BT(.*?)ET', stream_data, re.DOTALL)
        if len(bt_blocks) < 10:
            continue  # skip non-page streams

        lines = []
        for bt in bt_blocks:
            font_match = re.search(rb'/(C\d+)\s+', bt)
            short_font = font_match.group(1).decode() if font_match else None

            tj_match = re.search(rb'<([0-9A-Fa-f]+)>\s*Tj', bt)
            if not tj_match:
                continue

            hex_str = tj_match.group(1)
            glyphs = [hex_str[i:i+4] for i in range(0, len(hex_str), 4)]

            full_font = font_name_map.get(short_font, '') if short_font else ''
            font_map = glyph_map.get(full_font, {})

            text = ''
            for g in glyphs:
                text += font_map.get(g, '')

            if text.strip():
                lines.append(text.strip())

        if lines:
            all_pages.append(''.join(lines))

    return '\n\n'.join(all_pages)

if __name__ == '__main__':
    fp = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        '~/Downloads/三色笔记/拆分/2026新版高项三色笔记（信息系统项目管理师）（拖移项目 01）.pdf')

    with open(fp, 'rb') as f:
        data = f.read()

    print("Step 1: Building font maps...")
    glyph_map, font_name_map = build_all_maps(data)
    print(f"  Total BaseFonts with CMap: {len(glyph_map)}")

    print("\nStep 2: Extracting text...")
    text = extract_all_text(data, glyph_map, font_name_map)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'pdf_extracted_output.txt')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"\nSaved: {out}")
    print(f"Total chars: {len(text)}")
    print(f"\n=== First 1000 chars ===\n{text[:1000]}")
    print(f"\n=== Last 500 chars ===\n{text[-500:]}")
