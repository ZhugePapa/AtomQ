#!/usr/bin/env python3
"""Convert **bold** → ==highlight== in all MD files and the generator script."""
import os, re

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '知识点集合')
count = 0

# Process all MD files
for root, dirs, files in os.walk(base):
    for fname in files:
        if not fname.endswith('.md'):
            continue
        path = os.path.join(root, fname)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = re.sub(r'\*\*(.+?)\*\*', r'==\1==', content)
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            count += 1
            print(f"  {fname}: {len(re.findall(r'\*\*(.+?)\*\*', content))} conversions")

# Process the generator script too
gen_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generate_ch01_cards.py')
if os.path.exists(gen_path):
    with open(gen_path, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = re.sub(r'\*\*(.+?)\*\*', r'==\1==', content)
    if new_content != content:
        with open(gen_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"\n  generate_ch01_cards.py: {len(re.findall(r'\*\*(.+?)\*\*', content))} conversions")

print(f"\nTotal MD files updated: {count}")

# Process JSON key_points / mnemonics
import json
jcount = 0
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
            if val and '**' in val:
                new_val = re.sub(r'\*\*(.+?)\*\*', r'==\1==', val)
                if new_val != val:
                    card[field] = new_val
                    changed = True
        if changed:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            jcount += 1
            print(f"  JSON {fname}")
print(f"Total JSON files updated: {jcount}")
