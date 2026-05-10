#!/usr/bin/env python3
"""Post-process: extract :::key and :::tip from MD files to JSON fields."""
import json, os, re

CARDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '知识点集合', 'chapters', 'ch_01', 'cards')

updated = 0
for fname in sorted(os.listdir(CARDS_DIR)):
    if not fname.endswith('.json'):
        continue
    json_path = os.path.join(CARDS_DIR, fname)
    md_path = os.path.join(CARDS_DIR, fname.replace('.json', '.md'))

    if not os.path.exists(md_path):
        continue

    with open(json_path, 'r', encoding='utf-8') as f:
        card = json.load(f)
    with open(md_path, 'r', encoding='utf-8') as f:
        md = f.read()

    # Extract :::key block
    key_match = re.search(r':::key\s*\n(.*?):::', md, re.DOTALL)
    if key_match:
        key_text = key_match.group(1).strip()
        card['key_points'] = key_text
        md = md.replace(key_match.group(0), '').strip()

    # Extract :::tip block
    tip_match = re.search(r':::tip\s*\n(.*?):::', md, re.DOTALL)
    if tip_match:
        tip_text = tip_match.group(1).strip()
        card['mnemonics'] = tip_text
        md = md.replace(tip_match.group(0), '').strip()

    # Clean up MD: remove triple blank lines
    md = re.sub(r'\n{3,}', '\n\n', md).strip() + '\n'

    card['has_key_content'] = bool(card.get('key_points', ''))

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(card, f, ensure_ascii=False, indent=2)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md)

    if key_match or tip_match:
        updated += 1
        kp_preview = card.get('key_points', '')[:50]
        mn_preview = card.get('mnemonics', '')[:50]
        print(f"  {fname}: key={bool(key_match)}, tip={bool(tip_match)}")
        if kp_preview:
            print(f"    key_points: {kp_preview}...")
        if mn_preview:
            print(f"    mnemonics: {mn_preview}...")

print(f"\nUpdated: {updated} cards")
