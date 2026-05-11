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

obj_pat = re.compile(rb'(\d+ \d+ obj.*?endobj)', re.DOTALL)
all_objs = {tuple(m.group(1).split(b' ')[:2]): m.group(1) for m in obj_pat.finditer(data)}
def find_obj(ref_str):
    parts = ref_str.split()
    return all_objs.get((parts[0].encode(), parts[1].encode()))

for obj in all_objs.values():
    for short_h, ref_h in re.findall(rb'/(C\d+)\s+(\d+ \d+ R)', obj):
        short = short_h.decode()
        if short != 'C5': continue
        font_obj = find_obj(ref_h.decode())
        tu = re.search(rb'/ToUnicode\s+(\d+ \d+ R)', font_obj)
        cmap_obj = find_obj(tu.group(1).decode())
        cmap_data = get_stream(cmap_obj)
        text = cmap_data.decode('latin-1', errors='replace')

        # Find the section around 006d - print 20 lines around it
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if '006d' in line:
                start = max(0, i-5)
                end = min(len(lines), i+15)
                print(f"Lines {start}-{end} around '006d':")
                for j in range(start, end):
                    print(f"  {j}: {lines[j]}")
                break

        # Count all hex entries in bfrange blocks
        bfranges = re.findall(r'(\d+) beginbfrange(.*?)endbfrange', text, re.DOTALL)
        total_entries = 0
        for count_str, block in bfranges:
            count = int(count_str)
            # Count actual hex entries in this block
            hex_entries = re.findall(r'<[0-9A-Fa-f]+>', block)
            total_entries += len(hex_entries) // 3  # Each entry has 3 hex codes
            if '006d' in block:
                print(f"\nBlock with {count} entries containing 006d:")
                print(f"  Hex entries found: {len(hex_entries)}")
                print(f"  First few: {hex_entries[:6]}")

        print(f"\nTotal hex groups in all bfrange blocks: {total_entries}")
        break
