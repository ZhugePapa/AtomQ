#!/usr/bin/env python3
"""Rebuild chapters 2-23 from color-aware OCR records.

Chapter 1 is curated separately and is intentionally preserved. The remaining
chapters are regenerated from the PDF OCR output so red OCR lines become
Markdown `==highlight==` in card bodies.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = ROOT / "content_package" / "public"
SUBJECT_ID = "high_itpmp"
SUBJECT_ROOT = PUBLIC_ROOT / "subjects" / SUBJECT_ID
CHAPTERS_ROOT = SUBJECT_ROOT / "chapters"
OCR_PATH = Path("/private/tmp/atomq_all_color_ocr.json")
SOURCE_ID = "pdf_2026_tricolor_high"
BUILD_TIME = "2026-05-13T00:00:00+08:00"

NOISE_PATTERNS = [
    "更多资料请",
    "环球课堂",
    "本章分值预测",
    "预计选择题",
    "不需要人真学",
    "确实不懂",
    "可以放弃",
    "考前把发的考点",
    "关键词进行记忆",
    "把教材原文",
    "把握关键词",
]

TINY_HEADERS = {
    "要素",
    "具体内容",
    "层次",
    "协议",
    "特点",
    "技术",
    "频段",
    "应用",
    "场景",
    "适用范围",
    "类型",
    "说明",
    "输入",
    "输出",
    "工具",
    "技术",
    "方法",
    "内容",
    "管理",
    "定义",
    "分层",
    "整体",
    "架构",
    "架构平面",
    "接口类型",
    "南向接口",
    "北向接口",
    "东西向接口",
}

TABLE_LABELS = {
    "应用层",
    "传输层",
    "网络层",
    "网络接口层",
    "控制层",
    "数据层",
    "数据平面",
    "控制平面",
    "应用平面",
    "南向接口",
    "北向接口",
    "东西向接口",
}

FORCE_TERMS = [
    "网络的作用范围",
    "个人局域网(PAN)",
    "局域网(LAN)",
    "城域网(MAN)",
    "广域网(WAN)",
    "公用网",
    "专用网",
    "物理层",
    "数据链路层",
    "网络层",
    "传输层",
    "会话层",
    "表示层",
    "应用层",
    "PPP 点对点协议",
    "ISDN 综合业务数字网",
    "xDSL",
    "DDN 数字专线",
    "FR 帧中继",
    "ATM 异步传输模式",
    "新型网络创新架构",
    "网络虚拟化",
    "软件编程",
    "定义和控制网络",
    "控制面与数据面分离",
    "数据与控制相分离",
    "开放的统一接口",
    "OpenFlow",
    "逻辑中心化",
    "可编程",
    "全局网络信息",
    "数据转发功能",
    "快速处理匹配的数据包",
    "转发规则",
    "南向接口",
    "北向接口",
    "东西向接口",
    "控制器",
    "流表",
]


@dataclass
class Line:
    text: str
    color: str
    page: int


@dataclass
class CardDraft:
    lines: list[Line] = field(default_factory=list)


@dataclass
class SectionDraft:
    title: str
    cards: list[CardDraft] = field(default_factory=list)


@dataclass
class ChapterDraft:
    number: int
    title: str
    sections: list[SectionDraft] = field(default_factory=list)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(text: str) -> str:
    replacements = {
        "0SI": "OSI",
        "TeInet": "Telnet",
        "OpenFIow": "OpenFlow",
        "F1ow": "Flow",
        "FIow": "Flow",
        "1T": "IT",
        "尤误": "无误",
        "雷求": "需求",
        "鬗求": "需求",
        "于系人": "干系人",
        "T审计": "IT审计",
        "于系": "干系",
        "千": "于",
        "（": "(",
        "）": ")",
        "，": "，",
        "；": "；",
        "：": "：",
        "－": "-",
        "—": "-",
        "“": "\"",
        "”": "\"",
    }
    text = text.strip()
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"第\s*(\d+)\s*页$", r"第\1页", text)
    text = re.sub(r"[太大女]\*+", "", text)
    return text.strip()


def strip_marker(text: str) -> str:
    text = re.sub(r"^\s*\d{1,3}、\s*", "", text)
    text = re.sub(r"^\s*\d{1,3}[.．]\s*", "", text)
    text = re.sub(r"^\s*[一二三四五六七八九十]+、\s*", "", text)
    text = re.sub(r"^\s*[①②③④⑤⑥⑦⑧⑨⑩]\s*", "", text)
    return text.strip()


def is_noise(text: str) -> bool:
    clean = normalize_text(text)
    if not clean:
        return True
    if any(pattern in clean for pattern in NOISE_PATTERNS):
        return True
    if re.fullmatch(r"第\d+页", clean):
        return True
    if clean in {"2026", "信息系统项目管理师", "软考高项", "目录"}:
        return True
    if clean in {"需", "求", "用", "协议。", "止。网", "构"}:
        return True
    return False


def chapter_heading(text: str) -> tuple[int, str] | None:
    match = re.match(r"^第\s*0?(\d{1,2})\s*章\s*[-—－]?\s*(.+)$", text)
    if not match:
        return None
    title = normalize_text(match.group(2)).strip("- ")
    return int(match.group(1)), title


def section_heading(text: str) -> str | None:
    clean = normalize_text(text)
    match = re.match(r"^\d{1,2}\.\s*\d{1,2}\s*(.{2,42})$", clean)
    if match:
        title = tidy_title(match.group(1))
        if valid_section_title(title):
            return title
        return None
    match = re.match(r"^([一二三四五六七八九十]+)、\s*(.{2,42})$", clean)
    if match and "：" not in clean and ":" not in clean:
        title = tidy_title(match.group(2))
        if valid_section_title(title):
            return title
    return None


def valid_section_title(title: str) -> bool:
    if len(title) < 2:
        return False
    if not re.search(r"[\u4e00-\u9fffA-Za-z]", title):
        return False
    if re.fullmatch(r"[0-9.%-]+", title):
        return False
    if any(token in title for token in ["美元", "英元", "万元", "亿元"]):
        return False
    return True


def is_card_start(text: str) -> bool:
    clean = normalize_text(text)
    return bool(re.match(r"^\d{1,3}、\s*", clean) or re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]\s*", clean))


def is_tiny_header(text: str) -> bool:
    return strip_marker(normalize_text(text)) in TINY_HEADERS


def tidy_title(text: str) -> str:
    text = strip_marker(normalize_text(text))
    text = remove_exam_refs(text)
    text = re.sub(r"^[【\[]|[】\]]$", "", text)
    text = re.sub(r"[。；;，,].*$", "", text)
    text = text.strip(" ：:-")
    text = re.sub(r"\s+", "", text)
    return text[:32] or "章节核心考点"


def remove_exam_refs(text: str) -> str:
    text = re.sub(r"[（(][^）)]*\d{2}\s*[上下][^）)]*[）)]", "", text)
    text = re.sub(r"[（(]\s*\d{2}\s*[上下]\s*[^）)]{0,12}[）)]", "", text)
    text = re.sub(r"\(\s*\d{2}\s*[上下]\s*[^)]{0,12}\)", "", text)
    text = re.sub(r"（\s*\d{2}\s*[上下]\s*[^）]{0,12}）", "", text)
    return text.strip()


def display_text(text: str, *, strip_number: bool = False) -> str:
    text = normalize_text(text)
    text = remove_exam_refs(text)
    text = re.sub(r"^[>＞]\s*", "", text)
    text = re.sub(r"太\s*大", "", text)
    text = re.sub(r"([\u4e00-\u9fffA-Za-z]{2,12})\d{1,2}[.．、]\s*\1", r"\1", text)
    if strip_number:
        text = strip_marker(text)
    text = re.sub(r"^\s*[•◆]\s*", "", text)
    text = text.replace("•", "；")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ；;")


def read_ocr_lines(path: Path) -> list[Line]:
    records = load_json(path)
    lines: list[Line] = []
    for record in records:
        text = normalize_text(record.get("text", ""))
        if is_noise(text):
            continue
        lines.append(Line(text=text, color=record.get("color", "black"), page=int(record.get("page", 0))))
    return lines


def parse_chapters(lines: list[Line]) -> list[ChapterDraft]:
    chapters: list[ChapterDraft] = []
    current_chapter: ChapterDraft | None = None
    current_section: SectionDraft | None = None
    current_card: CardDraft | None = None

    def flush_card() -> None:
        nonlocal current_card
        if current_section and current_card and meaningful_card(current_card):
            current_section.cards.append(current_card)
        current_card = None

    def flush_section() -> None:
        nonlocal current_section
        flush_card()
        if current_chapter and current_section and current_section.cards:
            current_chapter.sections.append(current_section)
        current_section = None

    def flush_chapter() -> None:
        nonlocal current_chapter
        flush_section()
        if current_chapter and current_chapter.sections:
            chapters.append(current_chapter)
        current_chapter = None

    for line in lines:
        ch = chapter_heading(line.text)
        if ch:
            flush_chapter()
            current_chapter = ChapterDraft(number=ch[0], title=ch[1])
            current_section = None
            current_card = None
            continue

        if current_chapter is None:
            continue

        section_title = section_heading(line.text)
        if section_title:
            flush_section()
            current_section = SectionDraft(title=section_title)
            current_card = None
            continue

        if current_section is None:
            current_section = SectionDraft(title="章节核心考点")

        if is_card_start(line.text) and current_card and meaningful_card(current_card):
            flush_card()
            current_card = CardDraft(lines=[line])
            continue

        if current_card is None:
            if is_tiny_header(line.text):
                continue
            current_card = CardDraft(lines=[line])
        else:
            current_card.lines.append(line)

    flush_chapter()
    return [chapter for chapter in chapters if chapter.number >= 2]


def meaningful_card(card: CardDraft) -> bool:
    text = "".join(line.text for line in card.lines)
    return len(strip_marker(text)) >= 12


def merge_wrapped(lines: list[Line]) -> list[Line]:
    merged: list[Line] = []
    for line in lines:
        text = normalize_text(line.text)
        if not text or is_tiny_header(text):
            continue
        if not merged:
            merged.append(Line(text=text, color=line.color, page=line.page))
            continue
        prev = merged[-1]
        prev_clean = prev.text
        starts_new = is_card_start(text) or bool(re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", text))
        table_like = text in TINY_HEADERS or text in TABLE_LABELS or len(text) <= 6
        prev_open = not re.search(r"[。！？；;：:)）]$", prev_clean)
        if not starts_new and not table_like and prev_open and len(prev_clean) < 110:
            color = "red" if "red" in {prev.color, line.color} else "black"
            merged[-1] = Line(text=prev_clean + text, color=color, page=prev.page)
        else:
            merged.append(Line(text=text, color=line.color, page=line.page))
    return merged


def split_list_terms(text: str) -> list[str]:
    terms: list[str] = []
    if not re.search(r"(包括|分为|划分为|主要有|主要包括|类型有)", text):
        return terms
    tail = re.split(r"(包括|分为|划分为|主要有|主要包括|类型有)[：:]?", text, maxsplit=1)[-1]
    tail = re.split(r"[。；;]", tail)[0]
    for raw in re.split(r"[、,，/]|和|及|以及", tail):
        item = raw.strip(" ：: ")
        item = re.sub(r"^(等|这些|其中)$", "", item).strip()
        if 2 <= len(item) <= 24 and not re.search(r"(负责|提供|采用|实现|进行|通过|可以|需要)", item):
            terms.append(item)
    return terms


def core_terms(text: str) -> list[str]:
    clean = display_text(text, strip_number=True)
    terms: list[str] = []
    for term in FORCE_TERMS:
        if term in clean:
            terms.append(term)

    terms.extend(split_list_terms(clean))

    label_match = re.match(r"^([^：:]{2,12})[：:]\s*", clean)
    if label_match and label_match.group(1) not in TINY_HEADERS:
        terms.append(label_match.group(1).strip())

    for match in re.finditer(r"[A-Za-z]{2,}(?:/[A-Za-z]{2,})?|\d{3}(?:\.\d+)?", clean):
        token = match.group(0)
        if token.upper() not in {"THE", "AND", "FOR"}:
            terms.append(token)

    phrase_patterns = [
        r"是一种([^，。；;]{2,18})",
        r"是([^，。；;]{2,14})的一种",
        r"具有([^，。；;]{2,18})",
        r"负责([^，。；;]{2,18})",
        r"采用([^，。；;]{2,18})",
        r"通过([^，。；;]{2,18})",
    ]
    for pattern in phrase_patterns:
        for match in re.finditer(pattern, clean):
            phrase = match.group(1).strip()
            if 2 <= len(phrase) <= 18:
                terms.append(phrase)

    dedup: list[str] = []
    for term in terms:
        term = term.strip(" ：:，,。；;")
        if len(term) < 2:
            continue
        if term in dedup:
            continue
        if any(term != old and term in old for old in dedup):
            continue
        dedup.append(term)
    dedup.sort(key=len, reverse=True)
    return dedup[:10]


def mark_terms(text: str, terms: list[str]) -> str:
    out = text
    protected = out.split("==")
    for term in terms:
        if not term:
            continue
        for index in range(0, len(protected), 2):
            protected[index] = protected[index].replace(term, f"=={term}==")
    return "==".join(protected)


def highlighted(line: Line, *, strip_number: bool = False) -> str:
    text = display_text(line.text, strip_number=strip_number)
    if line.color == "red":
        return mark_terms(text, core_terms(text))
    return text


def clean_display_lines(card: CardDraft) -> list[Line]:
    lines = merge_wrapped(card.lines)
    result: list[Line] = []
    seen = set()
    for line in lines:
        text = normalize_text(line.text)
        if is_noise(text) or is_tiny_header(text) or text in TABLE_LABELS:
            continue
        key = strip_marker(text)
        if key in seen:
            continue
        seen.add(key)
        result.append(Line(text=text, color=line.color, page=line.page))
    return result


def split_long_lines(lines: list[Line]) -> list[list[Line]]:
    chunks: list[list[Line]] = []
    current: list[Line] = []
    current_len = 0
    for line in lines:
        text_len = len(line.text)
        starts_soft_boundary = (
            is_card_start(line.text)
            or bool(re.match(r"^\d{1,2}[.．]\s*", line.text))
            or line.color == "red"
        )
        if current and current_len >= 1400 and starts_soft_boundary:
            chunks.append(current)
            current = []
            current_len = 0
        if current and len(current) >= 16 and current_len >= 1000:
            chunks.append(current)
            current = []
            current_len = 0
        current.append(line)
        current_len += text_len
    if current:
        chunks.append(current)
    return chunks


def card_title(lines: list[Line], section_title: str) -> str:
    for line in lines:
        title = tidy_title(line.text)
        if title and title not in TINY_HEADERS and len(title) >= 2:
            return title[:30]
    return section_title[:30] or "章节考点"


def line_score(line: Line) -> int:
    text = normalize_text(line.text)
    score = 2 if line.color == "red" else 0
    for token in ["包括", "分为", "主要", "必须", "核心", "输入", "输出", "工具", "技术", "过程", "原则", "步骤"]:
        if token in text:
            score += 1
    if is_card_start(text):
        score += 1
    return score


def make_markdown(lines: list[Line]) -> str:
    if not lines:
        return "#### 概述\n\n待补充。\n"
    special = make_special_markdown(lines)
    if special:
        return special

    overview = highlighted(lines[0], strip_number=True)
    core_lines = lines[1:]
    bullets = []
    for line in core_lines:
        text = highlighted(line, strip_number=True)
        if text:
            bullets.append(f"- {text}")
    red_lines = []
    seen = set()
    for line in sorted(core_lines, key=line_score, reverse=True):
        if line.color != "red":
            continue
        terms = core_terms(line.text)
        if not terms:
            continue
        text = "、".join(f"=={term}==" for term in terms[:6])
        if text in seen:
            continue
        seen.add(text)
        red_lines.append(f"- {text}")
        if len(red_lines) >= 4:
            break

    parts = ["#### 概述", "", overview]
    if bullets:
        parts.extend(["", "#### 核心内容", "", *bullets])
    if red_lines:
        parts.extend(["", "#### 考试抓手", "", *red_lines])
    return "\n".join(parts).strip() + "\n"


def make_special_markdown(lines: list[Line]) -> str | None:
    joined = "\n".join(line.text for line in lines)
    title = tidy_title(lines[0].text) if lines else ""
    if "TCP/IP" in joined:
        return "\n".join(
            [
                "#### 概述",
                "",
                "TCP/IP 协议族按层次组织常见网络协议，考试重点是==层次与协议对应关系==。",
                "",
                "#### 协议分层",
                "",
                "| 层次 | 重点协议 / 作用 |",
                "|:---|:---|",
                "| ==应用层== | ==FTP==、==TFTP==、==HTTP==、==SMTP==、==DHCP==、==Telnet==、==DNS==、==SNMP== |",
                "| ==传输层== | ==TCP== 和 ==UDP==，负责流量控制、错误校验和排序服务 |",
                "| ==网络层== | ==IP==、==ICMP==、==IGMP==、==ARP==、==RARP== |",
                "| ==网络接口层== | 传输数据的物理媒介，也为网络层提供线路 |",
                "",
                "#### 考试抓手",
                "",
                "看到协议名，先定位到对应层次；尤其注意 ==TCP/UDP 属于传输层==，==IP/ICMP/ARP 属于网络层==。",
            ]
        ).strip() + "\n"

    if "软件定义网络" in joined or "SDN" in title:
        return "\n".join(
            [
                "#### 概述",
                "",
                "SDN 是一种==新型网络创新架构==，也是==网络虚拟化==的一种实现方式。它通过==软件编程==来==定义和控制网络==，核心思想是将网络设备的==控制面与数据面分离==。",
                "",
                "#### 分层",
                "",
                "| 层次 | 作用 |",
                "|:---|:---|",
                "| ==控制层== | 具有==逻辑中心化==、==可编程==的控制器，掌握==全局网络信息==，便于管理配置网络和部署新协议 |",
                "| ==数据层== | 哑交换机负责简单的==数据转发功能==，可以==快速处理匹配的数据包== |",
                "",
                "#### 架构平面",
                "",
                "| 平面 | 作用 |",
                "|:---|:---|",
                "| ==数据平面== | 由交换机等网络通用硬件组成，形成 SDN 数据通路 |",
                "| ==控制平面== | 逻辑中心化的 SDN 控制器，负责各种==转发规则==的控制 |",
                "| ==应用平面== | 各类 SDN 网络应用，用户无须关心底层细节即可编程、部署新应用 |",
                "",
                "#### 接口",
                "",
                "| 接口 | 作用 |",
                "|:---|:---|",
                "| ==南向接口== | 控制平面与数据平面通信，主流协议是 ==OpenFlow== |",
                "| ==北向接口== | 控制平面与应用平面通信，支持按需开发网络管理应用 |",
                "| ==东西向接口== | 多控制器之间通信，支持扩展、负载均衡和性能提升 |",
                "",
                "#### 考试抓手",
                "",
                "记住主线：==控制与数据分离==，控制器集中下发==转发规则==，南向接口常考 ==OpenFlow==。",
            ]
        ).strip() + "\n"
    return None


def label_rows(lines: list[Line]) -> list[tuple[str, str]]:
    rows = []
    for line in lines:
        text = strip_marker(display_text(line.text))
        match = re.match(r"^([^：:]{2,14})[：:]\s*(.{2,80})$", text)
        if match and match.group(1) not in TINY_HEADERS:
            rows.append((match.group(1).strip(), match.group(2).strip()))
    dedup = []
    seen = set()
    for label, desc in rows:
        if label in seen:
            continue
        seen.add(label)
        dedup.append((label, desc))
    return dedup


def make_key_points(lines: list[Line]) -> str:
    special = make_special_key_points(lines)
    if special is not None:
        return special

    rows = label_rows(lines)
    if 3 <= len(rows) <= 8:
        table = ["| 关键词 | 考点 |", "|:---|:---|"]
        table.extend(f"| =={label}== | {desc} |" for label, desc in rows)
        return "\n".join(table)

    red = []
    seen = set()
    for line in lines:
        if line.color != "red":
            continue
        terms = core_terms(line.text)
        if not terms:
            continue
        text = "、".join(f"=={term}==" for term in terms[:6])
        if text in seen:
            continue
        seen.add(text)
        red.append(f"- {text}")
        if len(red) >= 4:
            break
    if len(red) >= 2:
        return "\n".join(red)
    return ""


def make_special_key_points(lines: list[Line]) -> str | None:
    joined = "\n".join(line.text for line in lines)
    title = tidy_title(lines[0].text) if lines else ""
    if "TCP/IP" in joined:
        return "\n".join(
            [
                "| 层次 | 必背协议 |",
                "|:---|:---|",
                "| ==应用层== | FTP、TFTP、HTTP、SMTP、DHCP、Telnet、DNS、SNMP |",
                "| ==传输层== | TCP、UDP |",
                "| ==网络层== | IP、ICMP、IGMP、ARP、RARP |",
                "| ==网络接口层== | 物理媒介 / 线路 |",
            ]
        )
    if "软件定义网络" in joined or "SDN" in title:
        return "\n".join(
            [
                "- SDN 核心：==控制面与数据面分离==。",
                "- 分层：==控制层==负责规则控制，==数据层==负责数据转发。",
                "- 接口：==南向接口==常考 ==OpenFlow==，==北向接口==面向应用，==东西向接口==连接多控制器。",
            ]
        )
    return None


def make_mnemonics(lines: list[Line], title: str) -> str:
    joined = "\n".join(line.text for line in lines)
    match = re.search(r"口诀[：:]\s*([^。；;\n]{2,40})", joined)
    if match:
        return match.group(1).strip()
    rows = label_rows(lines)
    sequence_title = any(token in title for token in ["生命周期", "过程", "步骤", "阶段", "等级", "体系", "要素"])
    labels = [label for label, _ in rows]
    if sequence_title and 3 <= len(labels) <= 6 and all(2 <= len(label) <= 8 for label in labels):
        return "按顺序记：**" + "、".join(labels) + "**。"
    return ""


def infer_card_type(title: str, lines: list[Line]) -> str:
    text = "\n".join(line.text for line in lines)
    if any(token in title for token in ["过程", "流程", "步骤", "生命周期"]):
        return "process"
    if any(token in title for token in ["区别", "对比", "比较"]):
        return "comparison"
    if any(token in text for token in ["公式", "计算", "挣值"]):
        return "formula"
    if "定义" in text[:120]:
        return "definition"
    return "concept"


def infer_difficulty(lines: list[Line]) -> int:
    text = "\n".join(line.text for line in lines)
    if len(text) > 900 or any(token in text for token in ["计算", "公式", "挣值", "案例", "论文"]):
        return 3
    if len(text) > 430 or any(token in text for token in ["过程", "输入", "输出", "工具", "技术"]):
        return 2
    return 1


def tags_for(chapter_title: str, section_title: str, title: str) -> list[str]:
    tags = []
    for tag in [chapter_title, section_title, title]:
        tag = tidy_title(tag)
        if tag and tag not in tags:
            tags.append(tag[:16])
    return tags[:5]


def rebuild_chapter(chapter: ChapterDraft) -> dict[str, object]:
    chapter_id = f"ch_{chapter.number:02d}"
    chapter_dir = CHAPTERS_ROOT / chapter_id
    cards_dir = chapter_dir / "cards"
    if cards_dir.exists():
        shutil.rmtree(cards_dir)
    cards_dir.mkdir(parents=True, exist_ok=True)

    section_meta = []
    sort_no = 0
    previous_point_id: str | None = None
    for section_index, section in enumerate(chapter.sections, start=1):
        section_id = f"sec_{section_index:02d}"
        section_count = 0
        for draft in section.cards:
            clean_lines = clean_display_lines(draft)
            if not clean_lines:
                continue
            for lines in split_long_lines(clean_lines):
                if not lines:
                    continue
                sort_no += 1
                section_count += 1
                point_id = f"{sort_no:03d}"
                stem = f"{chapter_id}_{section_id}_{point_id}"
                title = card_title(lines, section.title)
                markdown = make_markdown(lines)
                key_points = make_key_points(lines)
                mnemonics = make_mnemonics(lines, title)
                pages = sorted({line.page for line in lines if line.page})
                card = {
                    "point_id": point_id,
                    "subject_id": SUBJECT_ID,
                    "chapter_id": chapter_id,
                    "section_id": section_id,
                    "title": title,
                    "card_type": infer_card_type(title, lines),
                    "difficulty": infer_difficulty(lines),
                    "estimated_read_seconds": min(360, max(60, int(len(markdown) / 3.5))),
                    "has_key_content": "==" in markdown,
                    "is_free": True,
                    "sort_no": sort_no,
                    "content_file": f"{stem}.md",
                    "content_md_path": f"subjects/{SUBJECT_ID}/chapters/{chapter_id}/cards/{stem}.md",
                    "tags": tags_for(chapter.title, section.title, title),
                    "key_points": key_points,
                    "mnemonics": mnemonics,
                    "warnings": "本卡片由颜色 OCR 自动整理，红字已转为 Markdown 重点标注；上线前仍建议抽样核对原文。",
                    "prerequisite_point_ids": [previous_point_id] if previous_point_id else [],
                    "related_point_ids": [],
                    "related_question_ids": [],
                    "source": "2026新版高项三色笔记（信息系统项目管理师）",
                    "source_type": "exam_note",
                    "source_refs": [{"source_id": SOURCE_ID, "page_label": ",".join(str(page) for page in pages) or "OCR自动定位待复核"}],
                    "author": "Codex color OCR 批量整理",
                    "reviewer": "待人工复核",
                    "review_status": "ai_draft",
                    "created_at": BUILD_TIME,
                    "updated_at": BUILD_TIME,
                    "version": 2,
                    "schema_version": 2,
                }
                write_json(cards_dir / f"{stem}.json", card)
                (cards_dir / f"{stem}.md").write_text(markdown, encoding="utf-8")
                previous_point_id = point_id

        if section_count:
            section_meta.append(
                {
                    "section_id": section_id,
                    "title": section.title,
                    "sort_no": len(section_meta) + 1,
                    "description": f"{chapter.title} - {section.title}",
                    "card_count": section_count,
                }
            )

    chapter_meta = {
        "chapter_id": chapter_id,
        "subject_id": SUBJECT_ID,
        "title": chapter.title,
        "description": f"{chapter.title}，由 PDF 颜色 OCR 自动整理为知识卡片草稿。",
        "sort_no": chapter.number,
        "card_count": sort_no,
        "sections": section_meta,
        "schema_version": 2,
    }
    write_json(chapter_dir / "chapter_meta.json", chapter_meta)
    return {"chapter_id": chapter_id, "title": chapter.title, "sort_no": chapter.number, "card_count": sort_no, "question_count": 0}


def update_indexes(generated: list[dict[str, object]]) -> None:
    subject_path = SUBJECT_ROOT / "subject_index.json"
    subject = load_json(subject_path)
    ch01 = [chapter for chapter in subject.get("chapters", []) if chapter.get("chapter_id") == "ch_01"]
    subject["chapters"] = sorted(ch01 + generated, key=lambda item: item["sort_no"])
    subject["updated_at"] = BUILD_TIME
    write_json(subject_path, subject)

    manifest_path = PUBLIC_ROOT / "manifest.json"
    manifest = load_json(manifest_path)
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
            "content_version": "2026.05.full-color-ocr-draft.1.public-full",
            "file_count": len(files),
            "files": files,
        },
    )


def main() -> None:
    lines = read_ocr_lines(OCR_PATH)
    chapters = parse_chapters(lines)
    generated = []
    seen_numbers = set()
    for chapter in chapters:
        if chapter.number == 1 or chapter.number in seen_numbers or "计算题考点汇总" in chapter.title:
            continue
        seen_numbers.add(chapter.number)
        generated.append(rebuild_chapter(chapter))
    update_indexes(generated)
    update_file_index()
    print(f"Rebuilt {len(generated)} chapters from color OCR")
    print(f"Rebuilt {sum(int(item['card_count']) for item in generated)} cards")


if __name__ == "__main__":
    main()
