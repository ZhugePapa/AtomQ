#!/usr/bin/env python3
import re

path = "/Users/leiwang/Documents/AtomQ/data/generate_ch01_cards.py"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Insert "", "" between tags array line and prereq array line
# Pattern: line like '    ["tag1","tag2"...],\n    ['
content = re.sub(
    r'(\s+\[".*?"\],\n)(\s+\[)',
    r'\1    "", "",\n\2',
    content
)

changes = 0
old_lines = open(path, 'r', encoding='utf-8').read().split('\n')
new_lines = content.split('\n')
for o, n in zip(old_lines, new_lines):
    if o != n:
        changes += 1

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Lines changed: {changes}")

idx = content.find('    "", "",')
if idx >= 0:
    print(f"First insertion at char {idx}:")
    print(content[max(0,idx-40):idx+70])
else:
    print("No insertions found. Sample context:")
    idx2 = content.find('["信息","物质"')
    if idx2 >= 0:
        print(repr(content[idx2:idx2+100]))
