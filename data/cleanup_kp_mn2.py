#!/usr/bin/env python3
import json, os, re

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '知识点集合')
for root, dirs, files in os.walk(base):
    for fname in files:
        if not fname.endswith('.json') or 'kp_' not in fname:
            continue
        path = os.path.join(root, fname)
        with open(path, 'r', encoding='utf-8') as f:
            card = json.load(f)
        changed = False
        for field in ('key_points', 'mnemonics'):
            val = card.get(field, '')
            if val:
                cleaned = re.sub(r'^\*\*.+?\*\*\s*', '', val)
                if cleaned != val:
                    card[field] = cleaned.strip()
                    changed = True
        if changed:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            print(f"  {fname}")
print("Done")
