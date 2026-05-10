#!/usr/bin/env python3
"""Clean key_points/mnemonics: strip redundant labels like '**记忆口诀**：'."""
import json, os, re

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '知识点集合')
updated = 0

for root, dirs, files in os.walk(base):
    for fname in files:
        if not fname.endswith('.json'):
            continue
        if 'kp_' not in fname:
            continue
        path = os.path.join(root, fname)
        with open(path, 'r', encoding='utf-8') as f:
            card = json.load(f)

        changed = False

        # Clean key_points
        kp = card.get('key_points', '')
        if kp:
            # Strip leading labels like "**高频考点**：" "**高频考点** " etc
            cleaned = re.sub(r'^\*\*[^*]+\*\*[：:\s]*', '', kp)
            if cleaned != kp:
                card['key_points'] = cleaned.strip()
                changed = True

        # Clean mnemonics
        mn = card.get('mnemonics', '')
        if mn:
            # Strip "**记忆口诀**：" etc
            cleaned = re.sub(r'^\*\*[^*]+\*\*[：:\s]*', '', mn)
            if cleaned != mn:
                card['mnemonics'] = cleaned.strip()
                changed = True

        if changed:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            updated += 1
            kp_new = card.get('key_points', '')[:60]
            mn_new = card.get('mnemonics', '')[:60]
            print(f"  {fname}: kp='{kp_new}' | mn='{mn_new}'")

print(f"\nUpdated: {updated} cards")
