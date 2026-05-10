import re, zlib

filepath = "/Users/leiwang/Downloads/三色笔记/拆分/2026新版高项三色笔记（信息系统项目管理师）（拖移项目 01）.pdf"
with open(filepath, 'rb') as f:
    data = f.read()

def get_stream(obj):
    sm = re.search(rb'stream\r?\n(.*?)endstream', obj, re.DOTALL)
    if not sm: return None
    raw = sm.group(1).rstrip()
    if b'/FlateDecode' in obj:
        try: return zlib.decompress(raw)
        except: return raw
    return raw

def parse_cmap(stream_data):
    text = stream_data.decode('latin-1', errors='replace')
    mapping = {}
    for _, ranges in re.findall(r'(\d+) beginbfrange\s*(.*?)\s*endbfrange', text, re.DOTALL):
        for s_h, e_h, u_h in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', ranges):
            s, e, u = int(s_h, 16), int(e_h, 16), int(u_h, 16)
            for i in range(e - s + 1):
                mapping[f'{s+i:04X}'] = chr(u + i)
    for _, chars in re.findall(r'(\d+) beginbfchar\s*(.*?)\s*endbfchar', text, re.DOTALL):
        for c_h, u_h in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', chars):
            mapping[c_h.upper()] = chr(int(u_h, 16))
    return mapping

obj_pat = re.compile(rb'(\d+ \d+ obj.*?endobj)', re.DOTALL)
all_objs = {tuple(m.group(1).split(b' ')[:2]): m.group(1) for m in obj_pat.finditer(data)}
def find_obj(ref_str):
    parts = ref_str.split()
    return all_objs.get((parts[0].encode(), parts[1].encode()))

# Find C2 and C5 CMaps
for obj in all_objs.values():
    for short_h, ref_h in re.findall(rb'/(C\d+)\s+(\d+ \d+ R)', obj):
        short = short_h.decode()
        if short not in ('C2', 'C5'):
            continue
        font_obj = find_obj(ref_h.decode())
        if not font_obj: continue
        tu = re.search(rb'/ToUnicode\s+(\d+ \d+ R)', font_obj)
        if not tu: continue
        cmap_obj = find_obj(tu.group(1).decode())
        if not cmap_obj: continue
        cmap_data = get_stream(cmap_obj)
        if not cmap_data: continue
        gm = parse_cmap(cmap_data)

        print(f"\n=== {short} CMap ({len(gm)} entries) ===")

        # Show raw CMap content
        raw_text = cmap_data.decode('latin-1', errors='replace')
        print(f"Raw (first 500 chars):\n{raw_text[:500]}")

        # Show sample entries
        for k, v in list(gm.items())[:10]:
            print(f"  {k} ({int(k,16)}) → U+{ord(v):04X} '{v}'")

        # Check specific codes used in BT blocks
        if short == 'C2':
            for code in ['0001', '0002', '0003', '0004', '0005', '0007', '0008', '0009']:
                print(f"  '{code}' in map: {code in gm}")
        if short == 'C5':
            for code in ['0018', '001f', '006d', '0046', '0001', '0003', '0004', '0019']:
                print(f"  '{code}' in map: {code in gm}")
