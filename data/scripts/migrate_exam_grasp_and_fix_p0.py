#!/usr/bin/env python3
"""Move Markdown exam-grasp sections into JSON key_points and fix P0 content issues."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = ROOT / "content_package" / "public"
SUBJECT_ID = "high_itpmp"
CHAPTERS_ROOT = PUBLIC_ROOT / "subjects" / SUBJECT_ID / "chapters"
BUILD_TIME = "2026-05-13T00:00:00+08:00"


TEXT_REPLACEMENTS = {
    "项日": "项目",
    "顶日": "项目",
    "篅求": "需求",
    "影晌": "影响",
    "考忠": "考虑",
    "不可旅今": "不可执行",
    "冬纸": "图纸",
    "J2BE": "J2EE",
    "可接控制": "可控",
    "包拮": "包括",
    "形响": "影响",
    "开台": "开始",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(text: str) -> str:
    for old, new in TEXT_REPLACEMENTS.items():
        text = text.replace(old, new)
    text = re.sub(r"[太女]{2,}|大大|大女女", "", text)
    text = re.sub(r"([一-龥]{2,12})大[；;]", r"\1；", text)
    text = re.sub(r"={4,}", "==", text)
    text = re.sub(r"==\s*(#{1,6}\s+)", r"\1", text)
    text = re.sub(r"^==-\s*(.+?)==", r"- ==\1==", text, flags=re.M)
    text = re.sub(r"(?m)^-\s*项目进度计划==", "- ==项目进度计划==", text)
    text = text.replace("==、==", "、")
    text = re.sub(r"([A-Za-z])==([A-Za-z+])", r"\1\2", text)
    text = re.sub(r"([A-Za-z])==\s*([+\-])", r"\1\2", text)
    text = re.sub(r"==([A-Za-z])==([A-Za-z])", r"==\1\2", text)
    text = re.sub(r"==([A-Za-z]+)==([+])", r"==\1\2", text)
    return text


def split_long_highlight(match: re.Match[str]) -> str:
    span = match.group(1).strip()
    if "\n" in span:
        return span
    if len(span) <= 60:
        return f"=={span}=="
    parts = [part.strip() for part in re.split(r"[、，,；;]", span) if part.strip()]
    if len(parts) >= 2 and all(len(part) <= 30 for part in parts):
        return "、".join(f"=={part}==" for part in parts)
    return span


def normalize_highlights(md: str) -> str:
    # Multiline highlights usually mean OCR/table text swallowed Markdown
    # structure. Keep the text, remove the broken hide marker.
    previous = None
    while previous != md:
        previous = md
        md = re.sub(r"==([^=\n]*\n.+?)==", lambda m: m.group(1), md, flags=re.S)
    md = re.sub(r"==([^=\n]+)==", split_long_highlight, md)
    return md


def clean_key_points(text: str) -> str:
    text = normalize_text(text or "").strip()
    text = re.sub(r"^####\s*考试抓手\s*", "", text, flags=re.M)
    text = re.sub(r"^==\s*", "", text)
    text = re.sub(r"\s*==$", "", text)
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == "-":
            continue
        line = re.sub(r"^-([^\s-])", r"- \1", line)
        line = re.sub(r"^-+", "-", line)
        line = normalize_text(line)
        lines.append(line)
    return "\n".join(lines).strip()


def compact_bad_key_point_line(line: str) -> str:
    raw = normalize_text(line)
    raw = raw.replace("==", " ")
    raw = re.sub(r"[-|]+", "、", raw)
    raw = re.sub(r"\s+", " ", raw)
    terms: list[str] = []
    for item in re.split(r"[、，,；;。/\n]", raw):
        item = item.strip(" -:：*|。()（）")
        if not (2 <= len(item) <= 26):
            continue
        if any(skip in item for skip in ["考试抓手", "解释说明", "本卡片", "关键词", "考点"]):
            continue
        if re.fullmatch(r"[0-9.]+", item):
            continue
        if item not in terms:
            terms.append(item)
    if not terms:
        return ""
    return "- " + "、".join(f"=={term}==" for term in terms[:8])


def sanitize_key_points(text: str) -> str:
    text = clean_key_points(text)
    if not text:
        return ""
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        is_table = line.startswith("|")
        bad = (
            "==-" in line
            or line.count("==") % 2 == 1
            or len(line) > 260
            or re.search(r"==[^=\n]{60,}", line) is not None
        )
        if bad and not is_table:
            compact = compact_bad_key_point_line(line)
            if compact:
                out.append(compact)
            continue
        out.append(normalize_text(line))
    dedup: list[str] = []
    seen = set()
    for line in out:
        key = line.replace("==", "")
        if key in seen:
            continue
        seen.add(key)
        dedup.append(line)
    return "\n".join(dedup).strip()


def merge_key_points(existing: str, moved: str) -> str:
    existing = sanitize_key_points(existing)
    moved = sanitize_key_points(moved)
    if not moved:
        return existing
    if not existing:
        return moved
    seen = {line.strip() for line in existing.splitlines() if line.strip()}
    additions = [line for line in moved.splitlines() if line.strip() and line.strip() not in seen]
    if not additions:
        return existing
    return existing.rstrip() + "\n" + "\n".join(additions)


EXAM_SECTION_RE = re.compile(
    r"\n*={0,2}####\s*考试抓手\s*\n+(.*?)(?=\n={0,2}####\s+|\Z)",
    re.S,
)


def move_exam_grasp(md: str) -> tuple[str, str]:
    moved_parts: list[str] = []

    def repl(match: re.Match[str]) -> str:
        moved_parts.append(match.group(1))
        return "\n"

    new_md = EXAM_SECTION_RE.sub(repl, md)
    return new_md, "\n".join(moved_parts)


def normalize_md(md: str) -> str:
    md = normalize_text(md).replace("\r\n", "\n")
    md = normalize_highlights(md)
    md = re.sub(r"^#{1,3}\s+", "#### ", md, flags=re.M)
    md = re.sub(r"^#{5,6}\s+", "#### ", md, flags=re.M)
    md = re.sub(r"(?m)^(####\s+(?:概述|核心内容|学习提示))(?=\S)", r"\1\n\n", md)
    md = re.sub(r"(?m)^-\s*", "- ", md)
    md = re.sub(r"(?m)^-\s*$", "", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def rewrite_ch10_030(cards_dir: Path) -> None:
    stem = "ch_10_sec_01_030"
    md_path = cards_dir / f"{stem}.md"
    json_path = cards_dir / f"{stem}.json"
    if not md_path.exists() or not json_path.exists():
        return
    md = """#### 概述

进度压缩是在==不缩减项目范围==的前提下缩短工期，常见方法是==赶工==和==快速跟进==。

#### 核心内容

- ==赶工==：通过增加资源、批准加班、增加额外资源或支付加急费用来压缩关键路径活动，可能增加成本和风险。
- ==快速跟进==：将原本顺序执行的活动或阶段改为部分并行，可能增加返工和风险。
- ==PERT / 三点估算==：用乐观时间、最可能时间、悲观时间估算活动工期；具体公式放在计算题专题学习。
- ==项目进度计划==：进度模型的输出，标明计划日期、持续时间、里程碑和所需资源。
- 常见进度图形：==横道图==看活动与日期，==里程碑图==看关键节点，==项目进度网络图==看活动逻辑关系。
- ==项目日历==：规定可以开展进度活动的工作日和工作班次。
"""
    data = load_json(json_path)
    data["title"] = "进度压缩与进度计划输出"
    data["card_type"] = "concept"
    data["estimated_read_seconds"] = 90
    data["tags"] = ["进度管理", "资源与进度优化", "进度压缩"]
    data["key_points"] = "\n".join(
        [
            "- ==赶工==：加资源压缩关键路径，常带来成本和风险上升。",
            "- ==快速跟进==：并行原本顺序执行的活动，常带来返工和风险上升。",
            "- ==进度图形==：横道图看日期，里程碑图看关键节点，网络图看逻辑关系。",
        ]
    )
    data["warnings"] = "已人工修复 OCR 污染、坏重点标记和长卡片问题。"
    data["updated_at"] = BUILD_TIME
    data["has_key_content"] = True
    md_path.write_text(md, encoding="utf-8")
    write_json(json_path, data)


def rewrite_ch05_061(cards_dir: Path) -> None:
    stem = "ch_05_sec_13_061"
    md_path = cards_dir / f"{stem}.md"
    json_path = cards_dir / f"{stem}.json"
    if not md_path.exists() or not json_path.exists():
        return
    md = """#### 概述

软件构件标准主要包括 ==CORBA==、==COM / DCOM / COM+==、==.NET== 和 ==J2EE==，考试重点是能识别这些标准及其定位。

#### 核心内容

- ==CORBA==：由 OMG 推动，目标是把对象技术和分布式系统技术集成为可互操作的统一结构。
- ==COM==：让不同开发人员、不同语言实现的对象能够被复用。
- ==DCOM==：COM 的分布式扩展，增强位置透明性、网络安全性和跨平台调用能力。
- ==COM+==：COM 的进一步发展，更强调与操作系统服务结合，把组件模型提升到应用层。
- ==.NET==：提供通用语言运行环境、基础类库、数据库访问和网络开发能力。
- ==J2EE==：用于构建可伸缩、灵活、易维护的企业级应用架构。
"""
    data = load_json(json_path)
    data["title"] = "软件构件标准"
    data["card_type"] = "comparison"
    data["estimated_read_seconds"] = 105
    data["tags"] = ["信息系统工程", "软件集成", "构件标准"]
    data["key_points"] = "\n".join(
        [
            "- 必认标准：==CORBA==、==COM / DCOM / COM+==、==.NET==、==J2EE==。",
            "- ==COM+== 更强调与操作系统服务结合；==J2EE== 面向企业级应用架构。",
        ]
    )
    data["warnings"] = "已人工修复 OCR 污染和坏重点标记。"
    data["updated_at"] = BUILD_TIME
    data["has_key_content"] = True
    md_path.write_text(md, encoding="utf-8")
    write_json(json_path, data)


def rewrite_known_ocr_cards() -> None:
    fixes = {
        "ch_11/cards/ch_11_sec_01_003": {
            "title": "成本类型",
            "md": """#### 概述

项目成本常见类型包括==可变成本==、==固定成本==、==直接成本==、==间接成本==、==机会成本==和==沉没成本==。

#### 核心内容

- ==可变成本==：随生产量、工作量或时间变化而变化。
- ==固定成本==：不随生产量、工作量或时间变化而变化。
- ==直接成本==：可直接归属于项目工作的成本，如差旅费、工资、物料和设备使用费。
- ==间接成本==：由多个项目共同分摊的一般管理费用，如税金、福利和保卫费用。
- ==机会成本==：选择一个方案后放弃的最佳替代方案收益。
- ==沉没成本==：过去已经发生、当前或未来决策无法改变的成本，决策时应排除其干扰。
""",
            "key_points": "- ==沉没成本==不应影响当前投资决策。\n- ==直接成本==归属单个项目，==间接成本==由多个项目分摊。",
        },
        "ch_11/cards/ch_11_sec_01_012": {
            "title": "项目资金需求",
            "md": """#### 概述

项目资金需求描述项目在不同时间段所需的资金投入，通常与==成本基准==和支出计划配合使用。

#### 核心内容

- 资金需求用于说明项目何时需要多少资金。
- 成本基准、支出计划和资金需求共同支持后续的==控制成本==。
""",
            "key_points": "- ==项目资金需求==关注资金投入的时间分布，不只是总成本。",
        },
        "ch_15/cards/ch_15_sec_01_024": {
            "title": "消极影响很高",
            "md": "#### 概述\n\n风险概率和影响矩阵中，风险影响可以分级；==消极影响很高==表示威胁对目标的影响非常严重。\n",
            "key_points": "- 风险矩阵要同时看==概率==和==影响==。",
        },
        "ch_15/cards/ch_15_sec_01_033": {
            "title": "决策树需求情景",
            "md": "#### 概述\n\n决策树分析会把不同需求情景纳入比较，用于在不确定条件下选择期望货币价值更优的方案。\n",
            "key_points": "- 决策树适合处理==不确定条件下的方案选择==。",
        },
        "ch_15/cards/ch_15_sec_03_080": {
            "title": "风险应对可执行性",
            "md": "#### 概述\n\n风险应对措施需要具备==可执行性==，否则即使记录在计划中，也难以真正降低威胁或提升机会。\n",
            "key_points": "- 风险应对不是写在文档里就结束，关键要能==落实执行==。",
        },
        "ch_10/cards/ch_10_sec_02_054": {
            "title": "储备分析与备选方案分析",
            "md": """#### 概述

进度管理中的数据分析常用==备选方案分析==和==储备分析==，用于比较方案并管理进度不确定性。

#### 核心内容

- ==备选方案分析==：比较不同资源能力、进度压缩技术、工具选择以及资源获取方式。
- ==应急储备==：包含在进度基准中，用于应对已识别并接受的风险。
- ==管理储备==：用于应对未知未知风险，通常不包含在进度基准中。
""",
            "key_points": "- ==应急储备==进基准，==管理储备==通常不进基准。",
        },
        "ch_15/cards/ch_15_sec_03_074": {
            "title": "风险登记册内容",
            "md": """#### 概述

风险登记册用于记录已识别风险及其后续分析、责任人和潜在应对措施。

#### 核心内容

- 已识别风险清单：按所需详细程度描述风险。
- 潜在风险责任人：识别风险时若已明确，可先记录，后续再确认。
- 潜在风险应对措施：若已形成初步应对思路，也可记录到风险登记册中。
""",
            "key_points": "- 风险登记册会随着风险管理过程持续更新。",
        },
        "ch_02/cards/ch_02_sec_04_043": {
            "title": "区块链加密与共识算法",
            "md": """#### 概述

区块链常考两类基础技术：==加密算法==和==共识机制==。

#### 核心内容

- ==散列算法 / 哈希算法==：可理解为数据指纹，典型算法包括 MD5、SHA-1、SHA-2、SM3；区块链常用 SHA-256。
- ==非对称加密算法==：常见算法包括 RSA、ElGamal、D-H、ECC。
- ==共识机制==：在没有中心协调的情况下，让分布式节点对区块数据变更达成一致。
- 常见共识机制包括 ==PoW==、==PoS==、==DPoS==、==Paxos==、==PBFT==。
- 评价共识机制时关注合规监管、性能效率、资源消耗和容错性。
""",
            "key_points": "- ==散列算法==用于数据指纹。\n- ==非对称加密==用于身份与数据安全。\n- ==共识机制==用于分布式节点达成一致。",
        },
        "ch_08/cards/ch_08_sec_01_031": {
            "title": "制定项目管理计划",
            "md": """#### 概述

制定项目管理计划是整合管理的重要过程，用于定义、准备和协调项目计划的所有组成部分，并整合为一份综合项目管理计划。

#### 核心内容

- 主要输入包括==项目章程==、其他规划过程的输出、事业环境因素和组织过程资产。
- 常用工具包括==专家判断==、数据收集、人际关系与团队技能和会议。
- 项目管理计划确定项目的执行、监控和收尾方式。
- 项目管理计划应基准化，至少包括范围、进度和成本方面的基准。
- 基准确定后，通常只能通过==变更请求==和==实施整体变更控制==进行更新。
""",
            "key_points": "- 项目管理计划是综合性计划，不是单一子计划。\n- 基准确定后，更新要走==整体变更控制==。",
        },
        "ch_10/cards/ch_10_sec_03_063": {
            "title": "三点估算",
            "md": """#### 概述

三点估算使用==乐观时间(To)==、==最可能时间(TM)==、==悲观时间(Tp)==来估算活动持续时间。

#### 核心内容

- 三角分布：`Te = (To + TM + Tp) / 3`。
- 贝塔分布：`Te = (To + 4TM + Tp) / 6`。
- 三点估算适合在持续时间存在不确定性时使用。
""",
            "key_points": "- 三角分布简单平均；贝塔分布给==最可能时间==更高权重。",
        },
        "ch_11/cards/ch_11_sec_02_032": {
            "title": "三点估算公式",
            "md": """#### 概述

成本估算中也可使用三点估算，常见形式包括==三角分布==和==贝塔分布==。

#### 核心内容

- 三角分布：`Ce = (Co + Cm + Cp) / 3`。
- 贝塔分布：`Ce = (Co + 4Cm + Cp) / 6`。
- 其中 `Co` 为乐观成本，`Cm` 为最可能成本，`Cp` 为悲观成本。
""",
            "key_points": "- 贝塔分布公式给==最可能成本== 4 倍权重。",
        },
        "ch_12/cards/ch_12_sec_01_035": {
            "title": "流程图与质量管理计划",
            "md": """#### 概述

流程图用于展示过程路径和整体处理顺序，质量管理计划用于说明如何实施质量政策、程序和指南以实现质量目标。

#### 核心内容

- ==流程图==有助于理解和估算过程的质量成本，识别可能出现质量缺陷的位置。
- ==SIPOC== 是一种常见流程视角，表示供应商、输入、过程、输出和客户。
- ==质量管理计划==是项目管理计划的组成部分，描述实现质量目标所需的活动和资源。
- 质量管理计划应在项目早期评审，以降低返工带来的成本超支和进度延误。
""",
            "key_points": "- ==SIPOC==：供应商、输入、过程、输出、客户。\n- 质量管理计划要尽早评审，减少返工。",
        },
    }
    for rel, payload in fixes.items():
        stem_path = CHAPTERS_ROOT / rel
        md_path = stem_path.with_suffix(".md")
        json_path = stem_path.with_suffix(".json")
        if not md_path.exists() or not json_path.exists():
            continue
        data = load_json(json_path)
        md_path.write_text(payload["md"], encoding="utf-8")
        data["title"] = payload["title"]
        data["key_points"] = sanitize_key_points(payload["key_points"])
        data["has_key_content"] = "==" in payload["md"]
        data["estimated_read_seconds"] = max(45, min(160, len(payload["md"]) // 4))
        data["warnings"] = "已人工修复 P0 OCR/标题/重点标记问题。"
        data["updated_at"] = BUILD_TIME
        data["tags"] = [tag for tag in data.get("tags", [])[:2] if tag] + [payload["title"]]
        write_json(json_path, data)


def process_all_cards() -> None:
    for json_path in sorted(CHAPTERS_ROOT.glob("ch_*/cards/*.json")):
        data = load_json(json_path)
        md_path = json_path.with_suffix(".md")
        if not md_path.exists():
            continue
        md = md_path.read_text(encoding="utf-8")
        md, moved_exam = move_exam_grasp(md)
        md = normalize_md(md)
        data["key_points"] = merge_key_points(data.get("key_points", ""), moved_exam)
        for key, value in list(data.items()):
            if isinstance(value, str):
                data[key] = normalize_text(value)
            elif isinstance(value, list):
                data[key] = [normalize_text(item) if isinstance(item, str) else item for item in value]
        data["key_points"] = sanitize_key_points(data.get("key_points", ""))
        data["has_key_content"] = "==" in md
        data["updated_at"] = BUILD_TIME
        md_path.write_text(md, encoding="utf-8")
        write_json(json_path, data)


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
    (PUBLIC_ROOT / "file_index.json").write_text(
        json.dumps(
            {
                "package_id": "atomq_high_itpmp_2026_public_full",
                "content_version": "2026.05.full-color-ocr-draft.3.exam-grasp-in-key-points",
                "file_count": len(files),
                "files": files,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def update_manifest() -> None:
    manifest_path = PUBLIC_ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["content_version"] = "2026.05.full-color-ocr-draft.3.exam-grasp-in-key-points"
    manifest["updated_at"] = BUILD_TIME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    process_all_cards()
    rewrite_ch10_030(CHAPTERS_ROOT / "ch_10" / "cards")
    rewrite_ch05_061(CHAPTERS_ROOT / "ch_05" / "cards")
    rewrite_known_ocr_cards()
    update_manifest()
    update_file_index()
    print("Moved Markdown 考试抓手 sections into JSON key_points and fixed P0 issues.")


if __name__ == "__main__":
    main()
