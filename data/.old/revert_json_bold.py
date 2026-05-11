#!/usr/bin/env python3
"""Revert ==highlight== → **bold** in JSON key_points/mnemonics only."""
import json, os, re

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '知识点集合')
count = 0

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
            if val and '==' in val:
                new_val = re.sub(r'==(.+?)==', r'**\1**', val)
                if new_val != val:
                    card[field] = new_val
                    changed = True
        if changed:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            count += 1
            print(f"  {fname}")

print(f"\nReverted: {count} cards")
