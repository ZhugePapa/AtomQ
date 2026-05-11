#!/usr/bin/env python3
"""Extract text from PDF using only stdlib (zlib for FlateDecode)."""
import re, zlib, sys, os

def extract_text(filepath, max_pages=None):
    with open(filepath, 'rb') as f:
        data = f.read()

    # Find all objects
    text_parts = []
    page_count = 0

    # Find stream objects
    obj_pattern = re.compile(rb'(\d+ \d+ obj.*?endobj)', re.DOTALL)
    for match in obj_pattern.finditer(data):
        obj = match.group(1)
        if max_pages and page_count >= max_pages:
            break
        # Check if it's a page object
        if b'/Type\s*/Page' in obj or b'/Type/Page' in obj:
            page_count += 1
        # Extract stream content
        stream_match = re.search(rb'stream\s+(.*?)\s*endstream', obj, re.DOTALL)
        if not stream_match:
            continue
        stream_data = stream_match.group(1).rstrip()
        # Decompress if FlateDecode
        if b'/FlateDecode' in obj or b'/FlateDecode' in data[match.start():match.start()+200]:
            try:
                stream_data = zlib.decompress(stream_data)
            except:
                pass
        # Extract text between BT and ET
        bt_blocks = re.findall(rb'BT\s*(.*?)\s*ET', stream_data, re.DOTALL)
        for block in bt_blocks:
            # Extract text from Tj, TJ, ' operators
            tj_texts = re.findall(rb'\((.*?)\)\s*Tj', block)
            for t in tj_texts:
                text_parts.append(t.decode('latin-1', errors='replace'))

            # TJ array: [(text) num (text) num ...] TJ
            tj_arrays = re.findall(rb'\[(.*?)\]\s*TJ', block, re.DOTALL)
            for arr in tj_arrays:
                arr_texts = re.findall(rb'\((.*?)\)', arr)
                for t in arr_texts:
                    text_parts.append(t.decode('latin-1', errors='replace'))

    return '\n'.join(text_parts)

if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        '~/Downloads/三色笔记/拆分/2026新版高项三色笔记（信息系统项目管理师）（拖移项目 01）.pdf')
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else None
    text = extract_text(filepath, max_pages)
    print(text)
