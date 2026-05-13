#!/usr/bin/env python3
"""Repair learning quality issues in the public knowledge-card package.

This post-process keeps the existing schema but makes generated OCR cards more
usable for mobile study:
- trims OCR noise and broken bullet fragments
- shortens noisy titles
- converts over-long highlights into compact memory anchors
- splits dense long cards into smaller cards
- merges tiny adjacent fragments inside the same chapter/section
- rebalances one-section project-management chapters into study sections
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = ROOT / "content_package" / "public"
SUBJECT_ID = "high_itpmp"
SUBJECT_ROOT = PUBLIC_ROOT / "subjects" / SUBJECT_ID
CHAPTERS_ROOT = SUBJECT_ROOT / "chapters"
BUILD_TIME = "2026-05-13T00:00:00+08:00"


OCR_REPLACEMENTS = {
    "0SI": "OSI",
    "TeInet": "Telnet",
    "OpenFIow": "OpenFlow",
    "F1ow": "Flow",
    "FIow": "Flow",
    "OTTO": "ITTO",
    "IIIIT": "IT",
    "IIII": "IT",
    "IIT审计": "IT审计",
    "尤误": "无误",
    "雷求": "需求",
    "鬗求": "需求",
    "于系人": "干系人",
    "于系": "干系",
    "文持": "支持",
    "作次": "作为",
    "T审计": "IT审计",
    "南此向": "南北向",
    "大大": "",
    "太女": "",
    "太大": "",
}

NOISE_LINE_PATTERNS = [
    r"^[重高]$",
    r"^\d{1,3}$",
    r"^[〇○]$",
    r"^第\d+页$",
    r"^更多资料请",
    r"环球课堂",
]

CORE_TERMS = [
    "输入", "输出", "工具与技术", "工具", "技术", "过程", "原则", "步骤", "方法", "目的",
    "关键路径法", "总浮动时间", "自由浮动时间", "资源平衡", "资源平滑", "进度压缩",
    "赶工", "快速跟进", "挣值", "PV", "EV", "AC", "SPI", "CPI", "BAC", "EAC", "ETC",
    "RACI", "责任分配矩阵", "风险登记册", "风险报告", "概率和影响矩阵", "应急储备", "管理储备",
    "质量审计", "因果图", "控制图", "帕累托图", "直方图", "散点图", "检查表",
    "沟通管理计划", "干系人参与计划", "采购管理计划", "合同", "变更请求",
    "项目章程", "项目管理计划", "范围基准", "进度基准", "成本基准", "绩效测量基准",
]

CHAPTER_SECTION_RULES: dict[str, list[tuple[str, list[str]]]] = {
    "ch_07": [
        ("项目建议与可行性研究", ["建议", "可行", "可研", "机会研究", "初步"]),
        ("项目评估与论证", ["评估", "论证", "评价", "专家"]),
        ("立项流程与文件", ["立项", "批复", "章程", "审批", "报告"]),
    ],
    "ch_08": [
        ("整合管理过程", ["过程", "整合", "整体"]),
        ("项目章程与计划", ["章程", "管理计划", "计划"]),
        ("指导执行与知识管理", ["指导", "执行", "知识", "管理项目知识"]),
        ("监控与变更控制", ["监控", "变更", "控制", "纠正", "预防"]),
        ("项目收尾", ["收尾", "结束", "验收"]),
    ],
    "ch_09": [
        ("范围管理过程", ["过程", "范围管理"]),
        ("需求收集与分析", ["需求", "访谈", "问卷", "原型", "引导"]),
        ("范围定义与 WBS", ["范围说明书", "WBS", "工作分解", "分解"]),
        ("确认与控制范围", ["确认范围", "控制范围", "验收", "偏差"]),
    ],
    "ch_10": [
        ("进度管理过程", ["过程", "进度管理"]),
        ("活动与网络图", ["活动", "紧前", "紧后", "网络图", "依赖"]),
        ("估算与进度计划", ["估算", "持续时间", "制定进度", "关键路径", "浮动"]),
        ("资源与进度优化", ["资源平衡", "资源平滑", "压缩", "赶工", "快速跟进"]),
        ("控制进度", ["控制进度", "偏差", "绩效", "趋势"]),
    ],
    "ch_11": [
        ("挣值与控制成本", ["挣值", "PV", "EV", "AC", "CPI", "SPI", "EAC", "ETC", "控制成本"]),
        ("估算与预算", ["估算", "预算", "成本基准", "储备", "资金需求", "成本汇总"]),
        ("成本管理过程", ["过程", "成本管理", "规划成本"]),
    ],
    "ch_12": [
        ("质量管理过程", ["过程", "质量管理"]),
        ("规划质量", ["规划质量", "质量管理计划", "质量测量指标"]),
        ("管理质量", ["管理质量", "审计", "过程分析"]),
        ("控制质量", ["控制质量", "检查", "测试", "核查"]),
        ("质量工具", ["因果图", "控制图", "帕累托", "直方图", "散点图", "检查表"]),
    ],
    "ch_13": [
        ("资源管理过程", ["过程", "资源管理"]),
        ("资源规划与估算", ["规划资源", "估算活动资源", "资源需求"]),
        ("获取与建设团队", ["获取资源", "建设团队", "培训", "团队建设"]),
        ("管理与控制资源", ["管理团队", "控制资源", "冲突", "绩效"]),
        ("责任分配与团队工具", ["RACI", "责任分配", "组织图", "矩阵"]),
    ],
    "ch_14": [
        ("沟通管理过程", ["过程", "沟通管理"]),
        ("规划沟通", ["规划沟通", "沟通管理计划", "沟通需求"]),
        ("管理沟通", ["管理沟通", "发布", "报告"]),
        ("监督沟通", ["监督沟通", "反馈", "绩效"]),
    ],
    "ch_15": [
        ("风险管理基础", ["风险的属性", "风险的分类", "风险成本", "管理基础", "目的"]),
        ("规划与识别风险", ["规划风险", "识别风险", "风险管理计划", "风险登记册", "风险来源", "风险描述"]),
        ("定性与定量分析", ["定性", "定量", "概率和影响", "敏感性", "龙卷风", "模拟", "决策树", "EMV"]),
        ("规划与实施风险应对", ["风险应对", "威胁应对", "机会应对", "应急储备", "转移", "规避", "减轻", "接受"]),
        ("监督风险", ["监督风险", "风险审计", "技术绩效分析", "储备分析"]),
    ],
    "ch_17": [
        ("干系人识别", ["识别", "登记册", "分析"]),
        ("干系人参与规划", ["规划", "参与计划", "参与度"]),
        ("管理与监督参与", ["管理", "监督", "参与", "沟通"]),
    ],
    "ch_19": [
        ("配置管理基础", ["配置", "配置项", "基线", "状态"]),
        ("变更管理流程", ["变更", "CCB", "请求", "批准", "实施"]),
        ("版本与发布管理", ["版本", "发布", "回退", "归档"]),
        ("监控审计与记录", ["审计", "记录", "报告", "跟踪"]),
    ],
}


@dataclass
class Card:
    json_path: Path
    md_path: Path
    data: dict
    md: str


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(text: str) -> str:
    for old, new in OCR_REPLACEMENTS.items():
        text = text.replace(old, new)
    text = re.sub(r"[太女]{2,}|大大|大女女", "", text)
    text = re.sub(r"I+T审计", "IT审计", text)
    text = re.sub(r"([一-龥]{2,12})大[；;]", r"\1；", text)
    text = text.replace("，", "，").replace("；", "；")
    text = re.sub(r"([一-龥])\s+([一-龥])", r"\1\2", text)
    text = re.sub(r"([A-Za-z])\s+([A-Za-z])", r"\1 \2", text)
    text = re.sub(r"([一-龥]{1,4})\d{1,2}[.．、]\s*([一-龥]{1,4})", r"\1\2", text)
    text = re.sub(r"点1\.核", "点。核", text)
    text = re.sub(r"术1\.项", "术。项", text)
    text = re.sub(r"划1\.项", "划。项", text)
    return text


def visible_text(md: str) -> str:
    text = re.sub(r"^#{1,6}\s*", "", md, flags=re.M)
    text = text.replace("==", "")
    text = re.sub(r"[|:\-\s]+", "", text)
    return text


def is_noise_line(line: str) -> bool:
    raw = line.strip().lstrip("-").strip()
    if raw.startswith("####"):
        return False
    if not raw:
        return False
    return any(re.search(pattern, raw) for pattern in NOISE_LINE_PATTERNS)


def title_from_text(text: str, fallback: str) -> str:
    clean = re.sub(r"==", "", normalize_text(text))
    clean = re.sub(r"^#{1,6}\s*", "", clean)
    clean = re.sub(r"^\s*[-\d.、①②③④⑤⑥⑦⑧⑨⑩]+\s*", "", clean)
    clean = clean.strip(" ：:，,。；;")
    if "：" in clean or ":" in clean:
        clean = re.split(r"[：:]", clean, maxsplit=1)[0]
    else:
        clean = re.split(r"[。；;，,]", clean, maxsplit=1)[0]
    clean = re.sub(r"\s+", "", clean)
    if len(clean) < 2 or re.fullmatch(r"\d+", clean):
        clean = fallback
    return clean[:22] or "章节考点"


def compact_highlight_span(span: str) -> str:
    clean = normalize_text(span).strip()
    if len(clean) <= 24 and not re.search(r"[。；;\n]", clean):
        return f"=={clean}=="

    terms: list[str] = []
    for term in CORE_TERMS:
        if term in clean and term not in terms:
            terms.append(term)
    for token in re.findall(r"[A-Z][A-Za-z0-9/]{1,12}|\d{3}(?:\.\d+)?", clean):
        if token not in terms:
            terms.append(token)
    for item in re.split(r"[、，,；;。]\s*", clean):
        item = item.strip(" ：:()（）")
        if 2 <= len(item) <= 12 and not re.search(r"(是|的|了|可以|需要|进行|通过|包括|以及)", item):
            if item not in terms:
                terms.append(item)
        if len(terms) >= 8:
            break
    if not terms:
        return clean
    out = clean.replace("==", "")
    for term in sorted(terms[:8], key=len, reverse=True):
        out = re.sub(rf"(?<!==){re.escape(term)}(?!==)", f"=={term}==", out, count=1)
    return out


def fix_highlights(text: str) -> str:
    parts = text.split("==")
    if len(parts) < 3:
        return text
    out: list[str] = []
    for index, part in enumerate(parts):
        if index % 2 == 0:
            out.append(part)
        else:
            out.append(compact_highlight_span(part))
    return "".join(out)


def clean_markdown(md: str) -> str:
    md = normalize_text(md).replace("\r\n", "\n")
    md = re.sub(r"={4,}", "==", md)
    md = re.sub(r"==\s*(\d{1,4})\s*==", r"\1", md)
    md = re.sub(r"^#{1,3}\s+", "#### ", md, flags=re.M)
    md = re.sub(r"^#{5,6}\s+", "#### ", md, flags=re.M)
    md = re.sub(r"^(####\s+(?:概述|核心内容|考试抓手|学习提示))(?=\S)", r"\1\n\n", md, flags=re.M)

    lines = md.splitlines()
    cleaned: list[str] = []
    for line in lines:
        if is_noise_line(line):
            continue
        raw = line.strip()
        if re.fullmatch(r"-\s*[一-龥A-Za-z]{1,2}", raw) and cleaned:
            cleaned[-1] = cleaned[-1].rstrip("。；;，,") + raw[1:].strip()
            continue
        if raw in {"-", "- 。"}:
            continue
        cleaned.append(line.rstrip())

    md = "\n".join(cleaned)
    md = re.sub(r"资\n-\s*源", "资源", md)
    md = re.sub(r"应\n-\s*对", "应对", md)
    md = re.sub(r"需\n-\s*求", "需求", md)
    md = re.sub(r"文\n-\s*持", "支持", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = fix_highlights(md)
    md = strip_artificial_wrappers(md)

    # Drop empty sections left by cleanup.
    md = re.sub(r"\n#### (核心内容|考试抓手|学习提示)\n\s*(?=\n#### |\Z)", "\n", md)
    if not md.strip().startswith("####"):
        md = "#### 概述\n\n" + md.strip()
    return md.strip() + "\n"


def strip_artificial_wrappers(md: str) -> str:
    """Remove generic repair prose if the script is re-run."""

    def clean_line(line: str) -> str:
        raw = line.strip()
        if raw.startswith("本卡片关注「") and "」：" in raw:
            title, rest = raw[len("本卡片关注「") :].split("」：", 1)
            rest = rest.strip()
            return rest or title
        if raw.startswith("本卡片延续「") and "，聚焦：" in raw:
            rest = raw.split("，聚焦：", 1)[1].strip()
            return rest.rstrip("。") + "。"
        if raw.startswith("本卡片汇总「"):
            matches = re.findall(r"「([^「」]{2,80})」", raw)
            focus = matches[-1] if matches else raw
            focus = re.sub(r"^本卡片关注「?|」?$", "", focus).strip()
            return focus or raw
        return line

    return "\n".join(clean_line(line) for line in md.splitlines())


def extract_sections(md: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = "概述"
    sections[current] = []
    for line in md.splitlines():
        match = re.match(r"^####\s+(.+)$", line)
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return sections


def first_content_line(md: str) -> str:
    for line in md.splitlines():
        raw = line.strip()
        if raw and not raw.startswith("####") and not raw.startswith("|:") and raw != "|":
            raw = raw.lstrip("-").strip()
            if raw.startswith("本卡片关注「") and "」：" in raw:
                title, rest = raw[len("本卡片关注「") :].split("」：", 1)
                raw = rest.strip() or title
            if raw.startswith("本卡片延续「") and "，聚焦：" in raw:
                raw = raw.split("，聚焦：", 1)[1].strip()
            if raw.startswith("本卡片汇总「"):
                matches = re.findall(r"「([^「」]{2,80})」", raw)
                raw = matches[-1] if matches else raw
            return raw
    return ""


def build_md(overview: str, bullets: list[str], exam: list[str] | None = None) -> str:
    parts = ["#### 概述", "", overview.strip()]
    if bullets:
        parts.extend(["", "#### 核心内容", ""])
        parts.extend(bullets)
    if exam:
        parts.extend(["", "#### 考试抓手", ""])
        parts.extend(exam)
    return "\n".join(parts).strip() + "\n"


def split_dense_card(card: Card) -> list[Card]:
    md = card.md
    if len(md) < 1050:
        return [card]
    sections = extract_sections(md)
    bullets = [line.strip() for line in sections.get("核心内容", []) if line.strip().startswith("- ")]
    if len(bullets) < 7:
        return [card]

    overview = "\n".join(line for line in sections.get("概述", []) if line.strip()).strip()
    exam = [line.strip() for line in sections.get("考试抓手", []) if line.strip().startswith("- ")]
    chunks = [bullets[i : i + 4] for i in range(0, len(bullets), 4)]
    if len(chunks) <= 1:
        return [card]

    result: list[Card] = []
    for index, chunk in enumerate(chunks, start=1):
        cloned = json.loads(json.dumps(card.data, ensure_ascii=False))
        focus = title_from_text(chunk[0], card.data.get("title", "章节考点"))
        cloned["title"] = focus
        cloned["key_points"] = "\n".join(chunk[:3]) if any("==" in item for item in chunk[:3]) else ""
        cloned["mnemonics"] = ""
        cloned["warnings"] = "由原密集卡片拆分，建议结合前后卡片学习。"
        chunk_overview = overview if index == 1 else f"本卡片延续「{card.data.get('title', '本节内容')}」，聚焦：=={focus}==。"
        cloned_md = build_md(chunk_overview, chunk, exam if index == len(chunks) else None)
        result.append(Card(card.json_path, card.md_path, cloned, clean_markdown(cloned_md)))
    return result


def is_tiny_card(card: Card) -> bool:
    text = visible_text(card.md)
    if len(text) >= 55:
        return False
    title = str(card.data.get("title", ""))
    return len(text) < 28 or len(title) < 4 or re.fullmatch(r"\d+", title or "")


def merge_tiny_cards(cards: list[Card]) -> list[Card]:
    result: list[Card] = []
    pending: Card | None = None
    for card in cards:
        if not is_tiny_card(card):
            if pending:
                result.append(pending)
                pending = None
            result.append(card)
            continue

        if pending and pending.data.get("section_id") == card.data.get("section_id"):
            p_title = pending.data.get("title", "章节片段")
            c_line = first_content_line(card.md)
            p_line = first_content_line(pending.md)
            merged_title = title_from_text(p_line, str(p_title))
            pending.data["title"] = merged_title
            pending.md = build_md(
                f"本卡片汇总「{merged_title}」相关的零散考点。",
                [f"- {p_line}", f"- {c_line}"],
            )
            pending.data["key_points"] = ""
            pending.data["mnemonics"] = ""
        else:
            c_line = first_content_line(card.md)
            card.md = build_md(
                f"本卡片关注「{card.data.get('title', '章节片段')}」：{c_line}",
                [],
            )
            pending = card
    if pending:
        result.append(pending)
    return result


def section_for_card(chapter_id: str, card: Card, fallback_title: str) -> str:
    rules = CHAPTER_SECTION_RULES.get(chapter_id)
    if not rules:
        return normalize_text(fallback_title)
    haystack = f"{card.data.get('title', '')}\n{visible_text(card.md)}"
    for title, keywords in rules:
        if any(keyword in haystack for keyword in keywords):
            return title
    return rules[0][0]


def retitle_card(card: Card, section_title: str) -> None:
    title = normalize_text(str(card.data.get("title", ""))).strip()
    bad = (
        not title
        or len(title) > 24
        or re.fullmatch(r"\d+", title)
        or title in {"章节核心考点", "核心内容", "具体内容"}
        or re.search(r"\d[.．、]\D{0,2}\d[.．、]", title) is not None
    )
    if bad:
        title = title_from_text(first_content_line(card.md), section_title)
    card.data["title"] = title[:22]


def quality_key_points(card: Card) -> None:
    kp = normalize_text(str(card.data.get("key_points", ""))).strip()
    kp = clean_markdown(kp).strip() if kp else ""
    if kp.startswith("#### 概述"):
        kp = kp.replace("#### 概述", "", 1).strip()
    if len(visible_text(kp)) < 12 or len(visible_text(kp)) > 520:
        kp = ""
    if "==" not in kp and len(kp) < 80:
        kp = ""
    card.data["key_points"] = kp

    memo = normalize_text(str(card.data.get("mnemonics", ""))).strip()
    if len(memo) > 120 or any(noise in memo for noise in ["太女", "大大"]):
        memo = ""
    card.data["mnemonics"] = memo


def update_card_flags(card: Card) -> None:
    card.data["has_key_content"] = "==" in card.md
    card.data["estimated_read_seconds"] = min(240, max(45, int(len(visible_text(card.md)) / 3.6)))
    card.data["updated_at"] = BUILD_TIME
    card.data["review_status"] = "ai_draft"
    card.data["warnings"] = "已做 OCR 噪声、标题、重点标注和卡片粒度修复；上线前仍建议抽样核对原 PDF。"
    tags = []
    for tag in card.data.get("tags", []):
        tag = normalize_text(str(tag)).strip()
        if tag and not re.fullmatch(r"\d+", tag) and tag not in tags:
            tags.append(tag[:16])
    title = str(card.data.get("title", ""))
    if title and title not in tags:
        tags.append(title[:16])
    card.data["tags"] = tags[:5]


def load_chapter_cards(chapter_id: str) -> list[Card]:
    cards_dir = CHAPTERS_ROOT / chapter_id / "cards"
    cards = []
    for json_path in sorted(cards_dir.glob("*.json")):
        data = load_json(json_path)
        md_path = cards_dir / data["content_file"]
        cards.append(Card(json_path, md_path, data, md_path.read_text(encoding="utf-8")))
    return cards


def rewrite_chapter(chapter_id: str) -> int:
    chapter_dir = CHAPTERS_ROOT / chapter_id
    chapter_meta = load_json(chapter_dir / "chapter_meta.json")
    old_cards = load_chapter_cards(chapter_id)
    processed: list[Card] = []
    for card in old_cards:
        card.md = clean_markdown(card.md)
        quality_key_points(card)
        for split_card in split_dense_card(card):
            processed.append(split_card)
    processed = merge_tiny_cards(processed)

    section_titles: list[str] = []
    for card in processed:
        old_section = next(
            (section["title"] for section in chapter_meta.get("sections", []) if section["section_id"] == card.data.get("section_id")),
            "章节核心考点",
        )
        section_title = section_for_card(chapter_id, card, old_section)
        if section_title not in section_titles:
            section_titles.append(section_title)
        card.data["_section_title"] = section_title
        retitle_card(card, section_title)
        update_card_flags(card)

    # Remove old files before rewriting a consistently renumbered chapter.
    cards_dir = chapter_dir / "cards"
    for path in cards_dir.glob("*"):
        path.unlink()

    section_id_by_title = {title: f"sec_{index:02d}" for index, title in enumerate(section_titles, start=1)}
    section_counts = {title: 0 for title in section_titles}
    previous_id: str | None = None
    for sort_no, card in enumerate(processed, start=1):
        point_id = f"{sort_no:03d}"
        section_title = card.data.pop("_section_title")
        section_id = section_id_by_title[section_title]
        section_counts[section_title] += 1
        stem = f"{chapter_id}_{section_id}_{point_id}"
        card.data["point_id"] = point_id
        card.data["chapter_id"] = chapter_id
        card.data["section_id"] = section_id
        card.data["sort_no"] = sort_no
        card.data["content_file"] = f"{stem}.md"
        card.data["content_md_path"] = f"subjects/{SUBJECT_ID}/chapters/{chapter_id}/cards/{stem}.md"
        card.data["prerequisite_point_ids"] = [previous_id] if previous_id else []
        card.data["related_point_ids"] = []
        card.md = clean_markdown(card.md)
        update_card_flags(card)
        write_json(cards_dir / f"{stem}.json", card.data)
        (cards_dir / f"{stem}.md").write_text(card.md, encoding="utf-8")
        previous_id = point_id

    chapter_meta["card_count"] = len(processed)
    chapter_meta["sections"] = [
        {
            "section_id": section_id_by_title[title],
            "title": normalize_text(title),
            "sort_no": index,
            "description": f"{chapter_meta['title']} - {normalize_text(title)}",
            "card_count": section_counts[title],
        }
        for index, title in enumerate(section_titles, start=1)
    ]
    write_json(chapter_dir / "chapter_meta.json", chapter_meta)
    return len(processed)


def update_indexes() -> None:
    subject = load_json(SUBJECT_ROOT / "subject_index.json")
    total = 0
    for chapter in subject.get("chapters", []):
        chapter_id = chapter["chapter_id"]
        meta = load_json(CHAPTERS_ROOT / chapter_id / "chapter_meta.json")
        chapter["card_count"] = meta["card_count"]
        chapter["title"] = meta["title"]
        total += meta["card_count"]
    subject["updated_at"] = BUILD_TIME
    write_json(SUBJECT_ROOT / "subject_index.json", subject)

    manifest_path = PUBLIC_ROOT / "manifest.json"
    manifest = load_json(manifest_path)
    if manifest.get("subjects"):
        manifest["subjects"][0]["card_count"] = total
    else:
        manifest["card_count"] = total
    manifest["chapters"] = [
        {
            "chapter_id": item["chapter_id"],
            "title": item["title"],
            "card_count": item["card_count"],
            "question_count": item.get("question_count", 0),
        }
        for item in subject["chapters"]
    ]
    manifest["updated_at"] = BUILD_TIME
    write_json(manifest_path, manifest)


def update_file_index() -> None:
    files = []
    for path in sorted(PUBLIC_ROOT.rglob("*")):
        if path.is_file() and path.name != "file_index.json":
            files.append(
                {
                    "path": path.relative_to(PUBLIC_ROOT).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    write_json(
        PUBLIC_ROOT / "file_index.json",
        {
            "package_id": "atomq_high_itpmp_2026_public_full",
            "content_version": "2026.05.full-color-ocr-draft.2.public-quality-repair",
            "file_count": len(files),
            "files": files,
        },
    )


def main() -> None:
    repaired = {}
    for chapter_dir in sorted(CHAPTERS_ROOT.glob("ch_*")):
        chapter_id = chapter_dir.name
        if chapter_id == "ch_01":
            continue
        repaired[chapter_id] = rewrite_chapter(chapter_id)
    update_indexes()
    update_file_index()
    print(json.dumps({"repaired_chapters": repaired, "total_cards": sum(repaired.values()) + load_json(CHAPTERS_ROOT / "ch_01" / "chapter_meta.json")["card_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
