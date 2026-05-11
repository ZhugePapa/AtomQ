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

# Find C5 CMap and debug parsing
for obj in all_objs.values():
    for short_h, ref_h in re.findall(rb'/(C\d+)\s+(\d+ \d+ R)', obj):
        short = short_h.decode()
        if short != 'C5': continue
        font_obj = find_obj(ref_h.decode())
        tu = re.search(rb'/ToUnicode\s+(\d+ \d+ R)', font_obj)
        cmap_obj = find_obj(tu.group(1).decode())
        cmap_data = get_stream(cmap_obj)

        text = cmap_data.decode('latin-1', errors='replace')

        # Count bfrange blocks
        bfranges = re.findall(r'(\d+) beginbfrange\s*(.*?)\s*endbfrange', text, re.DOTALL)
        print(f"bfrange blocks found: {len(bfranges)}")
        for count, _ in bfranges:
            print(f"  block with {count} entries")

        # Check for any line matching <006d>
        if '<006d>' in text:
            print("\n<006d> FOUND in CMap raw text")
            idx = text.index('<006d>')
            print(text[max(0,idx-50):idx+50])
        else:
            print("\n<006d> NOT found in CMap")

        # Parse and check entry count
        gm = parse_cmap(cmap_data)
        print(f"\nParsed entries: {len(gm)}")

        # Check max code
        max_code = max(int(k, 16) for k in gm.keys())
        print(f"Max code: {max_code} ({max_code:04X})")

        # Check specific codes
        for code in ['0018', '001f', '006d', '0046', '0093', '0025']:
            in_map = code in gm
            if in_map:
                print(f"  {code} → U+{ord(gm[code]):04X} '{gm[code]}'")
            else:
                print(f"  {code} → NOT IN MAP")
        break
