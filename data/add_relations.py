import json, os

base = "/Users/leiwang/Documents/AtomQ/data/content_package/public/subjects/high_itpmp/chapters/ch_01/cards"

relations = {
    "002": {"prereq": ["001"], "related": []},
    "003": {"prereq": ["001"], "related": ["004"]},
    "004": {"prereq": ["001"], "related": ["003"]},
    "005": {"prereq": ["001"], "related": ["006"]},
    "006": {"prereq": ["005"], "related": []},
    "007": {"prereq": ["005"], "related": ["008"]},
    "008": {"prereq": ["007"], "related": ["007"]},
    "009": {"prereq": ["001"], "related": ["010"]},
    "010": {"prereq": ["009"], "related": ["011"]},
    "011": {"prereq": ["010"], "related": []},
    "012": {"prereq": ["003"], "related": []},
    "014": {"prereq": ["011"], "related": []},
    "015": {"prereq": [], "related": ["016", "017"]},
    "016": {"prereq": ["015"], "related": []},
    "017": {"prereq": ["015"], "related": []},
    "018": {"prereq": [], "related": ["019"]},
    "019": {"prereq": [], "related": ["018", "020"]},
    "020": {"prereq": ["019"], "related": []},
    "022": {"prereq": [], "related": ["023"]},
    "023": {"prereq": ["022"], "related": ["024"]},
    "024": {"prereq": ["023"], "related": ["025"]},
    "025": {"prereq": ["024"], "related": []},
    "026": {"prereq": ["025"], "related": []},
    "027": {"prereq": ["019"], "related": ["028"]},
    "028": {"prereq": ["027"], "related": []},
}

updated = 0
for fname in sorted(os.listdir(base)):
    if not fname.endswith('.json'):
        continue
    path = os.path.join(base, fname)
    with open(path, 'r', encoding='utf-8') as f:
        card = json.load(f)
    pid = card["point_id"]
    if pid in relations:
        rel = relations[pid]
        old_pre = card.get("prerequisite_point_ids", [])
        old_rel = card.get("related_point_ids", [])
        if old_pre != rel["prereq"] or old_rel != rel["related"]:
            card["prerequisite_point_ids"] = rel["prereq"]
            card["related_point_ids"] = rel["related"]
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            updated += 1
            print(f"  {fname}: pre={rel['prereq']}, rel={rel['related']}")

print(f"\nUpdated: {updated} cards")
