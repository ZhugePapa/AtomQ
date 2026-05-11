#!/usr/bin/env python3
"""Refactor card generator: add key_points/mnemonics, extract from MD."""
import re

path = "/Users/leiwang/Documents/AtomQ/data/generate_ch01_cards.py"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update write_json signature
content = content.replace(
    'def write_json(point_id, chapter_id, section_id, title, card_type, difficulty, est_read,\n'
    '               has_key, is_free, sort, content_file, tags,\n'
    '               prereq, related, related_q, source, source_type):',
    'def write_json(point_id, chapter_id, section_id, title, card_type, difficulty, est_read,\n'
    '               has_key, is_free, sort, content_file, tags,\n'
    '               key_points, mnemonics,\n'
    '               prereq, related, related_q, source, source_type):'
)

# 2. Add key_points/mnemonics to JSON data dict
content = content.replace(
    '        "tags": tags,\n'
    '        "prerequisite_point_ids": prereq,',
    '        "tags": tags,\n'
    '        "key_points": key_points,\n'
    '        "mnemonics": mnemonics,\n'
    '        "prerequisite_point_ids": prereq,'
)

# 3. Update card() signature
content = content.replace(
    'def card(point_id, section_id, title, card_type, difficulty, est_read, has_key, is_free,\n'
    '         sort, tags, prereq, related, related_q, source, source_type, md_content):',
    'def card(point_id, section_id, title, card_type, difficulty, est_read, has_key, is_free,\n'
    '         sort, tags, key_points, mnemonics, prereq, related, related_q, source, source_type, md_content):'
)

# 4. Update card() body to pass key_points/mnemonics
content = content.replace(
    '    write_json(point_id, CH, section_id, title, card_type, difficulty, est_read, has_key,\n'
    '               is_free, sort, cf, tags, prereq, related, related_q, source, source_type)',
    '    write_json(point_id, CH, section_id, title, card_type, difficulty, est_read, has_key,\n'
    '               is_free, sort, cf, tags, key_points, mnemonics, prereq, related, related_q, source, source_type)'
)

# 5. For each card() call, extract :::key and :::tip, add key_points/mnemonics params
# Pattern: card(..."tags",\n        [...]...source_type,\n        """...""")
# We need to insert key_points and mnemonics between tags and prereq

def process_card(match):
    full = match.group(0)
    # Extract MD content (last argument after source_type)
    parts = full.split(',\n    """')
    if len(parts) < 2:
        return full
    md_part = parts[-1]
    # Find the closing """
    end_idx = md_part.rfind('"""')
    if end_idx < 0:
        return full
    md_content = md_part[:end_idx]

    # Extract :::key block
    key_match = re.search(r':::key\s*\n(.*?):::', md_content, re.DOTALL)
    key_points = ''
    if key_match:
        key_text = key_match.group(1).strip()
        # Escape any quotes in the text
        key_points = key_text.replace('"', '\\"')
        # Remove from MD
        md_content = md_content.replace(key_match.group(0), '').strip()

    # Extract :::tip block
    tip_match = re.search(r':::tip\s*\n(.*?):::', md_content, re.DOTALL)
    mnemonics = ''
    if tip_match:
        tip_text = tip_match.group(1).strip()
        mnemonics = tip_text.replace('"', '\\"')
        md_content = md_content.replace(tip_match.group(0), '').strip()

    if not key_points and not mnemonics:
        return full  # No changes needed

    # Clean up md_content - remove extra blank lines
    md_content = re.sub(r'\n{3,}', '\n\n', md_content).strip()

    # Rebuild: insert key_points and mnemonics between tags and prereq
    # Find the position after tags array and before prereq
    # The format is: ...tags,\n        [...],\n        [...],\n        "source",...
    # Actually: sort, tags,\n        [...],  <-- prereq
    #           [...] <-- related
    #           [...] <-- related_q
    #           "source_type", "official",\n        """..."""

    # Simpler approach: insert before the prereq array line
    # Find the line with "prereq" pattern - it's an array like [], [...], or ["..."]
    prereq_pattern = r'(\n\s*)(\[[^\]]*\],\s*\n\s*\[[^\]]*\],\s*\n\s*\[[^\]]*\],)'
    insert = f'\\1"{key_points}", "{mnemonics}",\\1\\2'
    full = re.sub(prereq_pattern, insert, full, count=1)

    # Update the MD content
    parts = full.split(',\n    """')
    if len(parts) >= 2:
        md_end = parts[-1].rfind('"""')
        if md_end >= 0:
            parts[-1] = md_content + parts[-1][md_end:]
        full = ',\n    """'.join(parts)

    return full

# Process each card block
# Find card(... """...""") blocks
# Using a simpler approach: process line by line for insertion, and MD separately

# Actually let me use a different approach.
# I'll insert key_points/mnemonics as string params right after the tags array.
# Pattern: tags array line ends with ],\n
# Next is either prereq or directly

# Let me find all card calls and process them individually
card_pattern = re.compile(
    r'(card\(\s*\n\s*"kp_ch01_\d{3}",\s*"sec_01_\d{2}",\s*"([^"]*)",[^)]*?"""[^)]*?"""\s*\)\s*)',
    re.DOTALL
)

# This is getting complex. Let me just modify the card calls directly.
# I'll add empty key_points="" and mnemonics="" before prereq for now,
# then the user can fill them in.

# Simpler approach: find the line pattern after tags:
#     ["tag1","tag2"],
#     [],    <-- prereq
# Replace with:
#     ["tag1","tag2"],
#     "","",    <-- key_points, mnemonics (empty for now)
#     [],

# Actually, the cleanest approach: insert right after the tags line
# Pattern: tags_array_line \n prereq_line
content = re.sub(
    r'(      \[.*tags.*\],\s*\n)\s*(\[\])',
    r'\1      "", "",\n      \2',
    content
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done. Added key_points/mnemonics params to card() signatures.")
print("Card calls have empty key_points='' and mnemonics='' placeholders.")
print("Run the generator, then manually fill in key_points and mnemonics.")
