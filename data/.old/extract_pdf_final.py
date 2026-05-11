#!/usr/bin/env python3
"""PDF text extractor — handles Chinese CID fonts with ToUnicode CMaps."""
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
    """Parse CMap stream → {hex_glyph: unicode_char}."""
    text = stream_data.decode('latin-1', errors='replace')
    mapping = {}
    # bfrange: start end unicode_start
    for _, ranges in re.findall(r'(\d+) beginbfrange\s*(.*?)\s*endbfrange', text, re.DOTALL):
        for start_h, end_h, uni_h in re.findall(
            r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', ranges):
            s, e, u = int(start_h, 16), int(end_h, 16), int(uni_h, 16)
            for i in range(e - s + 1):
                mapping[f'{s+i:04X}'] = chr(u + i)
    # bfchar: code unicode
    for _, chars in re.findall(r'(\d+) beginbfchar\s*(.*?)\s*endbfchar', text, re.DOTALL):
        for code_h, uni_h in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', chars):
            mapping[code_h.upper()] = chr(int(uni_h, 16))
    return mapping

def extract(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    obj_pat = re.compile(rb'(\d+ \d+ obj.*?endobj)', re.DOTALL)
    all_objs = {tuple(m.group(1).split(b' ')[:2]): m.group(1) for m in obj_pat.finditer(data)}

    def find_obj(ref_str):
        parts = ref_str.split()
        key = (parts[0].encode(), parts[1].encode())
        obj = all_objs.get(key)
        return obj

    # Step 1: Font resource → BaseFont → CMap
    short_to_glyphmap = {}

    for obj in all_objs.values():
        # Find font resource entries: /C2 16 0 R
        for short_h, ref_h in re.findall(rb'/(C\d+)\s+(\d+ \d+ R)', obj):
            short = short_h.decode()
            if short in short_to_glyphmap:
                continue
            font_obj = find_obj(ref_h.decode())
            if not font_obj:
                continue
            # Get ToUnicode ref from font object
            tu = re.search(rb'/ToUnicode\s+(\d+ \d+ R)', font_obj)
            if not tu:
                continue
            cmap_obj = find_obj(tu.group(1).decode())
            if not cmap_obj:
                continue
            cmap_data = get_stream(cmap_obj)
            if not cmap_data:
                continue
            gm = parse_cmap(cmap_data)
            if gm:
                short_to_glyphmap[short] = gm
                bf = re.search(rb'/BaseFont\s*/(\S+)', font_obj)
                bf_name = bf.group(1).decode() if bf else '?'
                print(f"  {short} → {len(gm):4d} glyphs  ({bf_name[:60]})")

    print(f"\nTotal fonts mapped: {len(short_to_glyphmap)}")

    # Step 2: Extract text from content streams
    all_pages = []
    for obj in all_objs.values():
        sd = get_stream(obj)
        if not sd:
            continue
        bt_blocks = re.findall(rb'BT(.*?)ET', sd, re.DOTALL)
        if len(bt_blocks) < 10:
            continue

        lines = []
        for bt in bt_blocks:
            font = re.search(rb'/(C\d+)\s+', bt)
            short = font.group(1).decode() if font else None
            gm = short_to_glyphmap.get(short, {}) if short else {}

            tj = re.search(rb'<([0-9A-Fa-f]+)>\s*Tj', bt)
            if not tj:
                continue

            hex_str = tj.group(1).decode().upper()
            glyphs = [hex_str[i:i+4] for i in range(0, len(hex_str), 4)]
            text = ''.join(gm.get(g, '') for g in glyphs)
            if text.strip():
                lines.append(text.strip())

        if lines:
            all_pages.append(''.join(lines))

    return '\n\n'.join(all_pages)

if __name__ == '__main__':
    fp = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        '~/Downloads/三色笔记/拆分/2026新版高项三色笔记（信息系统项目管理师）（拖移项目 01）.pdf')
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdf_extracted_output.txt')

    text = extract(fp)

    with open(out, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"\nSaved: {out}")
    print(f"Chars: {len(text)}, Lines: {len(text.splitlines())}")
    print(f"\n=== First 1500 chars ===\n{text[:1500]}")
