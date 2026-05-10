#!/usr/bin/env python3
"""Downgrade all ATX headings in MD files by one level: ## → ###, etc."""
import os, re

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '知识点集合')
count = 0

for root, dirs, files in os.walk(base):
    for fname in files:
        if not fname.endswith('.md'):
            continue
        path = os.path.join(root, fname)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        def downgrade(m):
            return '#' + m.group(0)

        new_content = re.sub(r'^#{2,}', downgrade, content, flags=re.MULTILINE)

        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            count += 1
            old_headings = re.findall(r'^(#{2,})\s', content, re.MULTILINE)
            new_headings = re.findall(r'^(#{3,})\s', new_content, re.MULTILINE)
            print(f"  {fname}: {len(old_headings)} headings: {set(old_headings)} → {set(new_headings)}")

print(f"\nTotal MD files updated: {count}")
