#!/usr/bin/env python3
import zipfile, xml.etree.ElementTree as ET

ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def parse_tstr(zf, sheet_path):
    tree = ET.parse(zf.open(sheet_path))
    root = tree.getroot()
    rows = []
    for row in root.findall('.//x:row', ns):
        cells = []
        for c in row.findall('x:c', ns):
            v = c.find('x:v', ns)
            cells.append(v.text if v is not None and v.text else '')
        if any(c for c in cells):
            rows.append(cells)
    return rows

with zipfile.ZipFile('软考刷题App_知识卡片数据字典_V1.1.xlsx', 'r') as zf:
    rows = parse_tstr(zf, 'xl/worksheets/sheet2.xml')

    print("=== users object ===")
    for r in rows:
        if r[0] == '用户账号' or (r[0] == '' and any('user_id' == r[3] or 'login_status' == r[3] or 'exam_date' == r[3] for _ in [1])):
            if r[3]:
                print(f"  {r[3]:25s} | {r[4]:10s} | {r[8]:50s}")

    print("\n=== chapter_meta fields ===")
    capture = False
    for r in rows:
        if r[1] == 'chapter_meta.json':
            capture = True
        elif capture and r[0] != '' and r[1] != 'chapter_meta.json':
            capture = False
        if capture and r[3]:
            print(f"  {r[3]:25s} | {r[4]:10s} | {r[8]:50s}")

    print("\n=== knowledge_point_ids ===")
    for r in rows:
        if r[3] == 'knowledge_point_ids':
            print(f"  Constraint: {r[7]}")
            print(f"  Note: {r[8]}")

    print("\n=== options ===")
    for r in rows:
        if r[3] == 'options':
            print(f"  Constraint: {r[7]}")
            print(f"  Note: {r[8]}")

    print("\n=== schema_version ===")
    for r in rows:
        if r[3] == 'schema_version':
            print(f"  Note: {r[8]}")
            print(f"  Remark: {r[10]}")

    print("\n=== exam_paper ===")
    for r in rows:
        if r[3] == 'paper_id':
            print("  (exam_paper fields:)")
        if r[1].startswith('exam_paper') or (r[0] == '静态真题卷' and r[3]):
            if r[3]:
                print(f"  {r[3]:25s} | {r[4]:10s} | {r[8]:45s}")

    print("\n=== Sheet 4 - New relations ===")
    rows4 = parse_tstr(zf, 'xl/worksheets/sheet4.xml')
    for r in rows4:
        src = r[0]
        if 'users' in src.lower() or 'exam_paper' in src.lower() or '新增' in src:
            print(f"  {r[0]:30s} | {r[2]:20s} | {r[4]:15s} | {r[5]}")
