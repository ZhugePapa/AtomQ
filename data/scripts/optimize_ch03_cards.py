#!/usr/bin/env python3
"""Curate chapter 3 knowledge cards from the 2026 tricolor notes."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = ROOT / "content_package" / "public"
SUBJECT_ID = "high_itpmp"
CHAPTER_ID = "ch_03"
CHAPTER_ROOT = PUBLIC_ROOT / "subjects" / SUBJECT_ID / "chapters" / CHAPTER_ID
CARDS_DIR = CHAPTER_ROOT / "cards"
BUILD_TIME = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
CONTENT_VERSION = "2026.05.full-color-ocr-draft.8.ch03-curated"


def md(text: str) -> str:
    return text.strip() + "\n"


CARDS = [
    {
        "point_id": "001",
        "section_id": "sec_01",
        "title": "IT治理目标",
        "card_type": "concept",
        "difficulty": 1,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "治理目标"],
        "key_points": "- 目标三件事：**业务一致、资源有效、风险管理**。\n- 题干问“IT治理目标”时，不要答成具体运维活动。",
        "mnemonics": "记作：**业资风**。",
        "md": md("""
### 概述

IT治理的主要目标是让信息技术真正服务组织目标，而不是让 IT 系统孤立运行。

### 核心内容

IT治理主要目标包括：==与业务目标一致==、==有效利用信息与数据资源==、==风险管理==。

### 易混点

- “与业务目标一致”强调 IT 战略和业务战略同向。
- “有效利用信息与数据资源”强调资源价值。
- “风险管理”强调识别、评估和控制 IT 相关风险。
"""),
    },
    {
        "point_id": "002",
        "section_id": "sec_01",
        "title": "管理层次三层",
        "card_type": "comparison",
        "difficulty": 1,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "管理层次"],
        "key_points": "- 三层：**最高管理层、执行管理层、业务与服务执行层**。\n- 选择题常考“谁负责战略、谁负责执行、谁负责服务交付”。",
        "mnemonics": "从上到下记：**高、执、业服**。",
        "md": md("""
### 概述

IT治理不是某一个 IT 部门单独完成的工作，而是分层协同的管理体系。

### 核心内容

| 层次 | 主要关注 |
|:---|:---|
| ==最高管理层== | 证实 IT 战略与业务战略一致，指导 IT 战略和投资方向 |
| ==执行管理层== | 制定 IT 目标，分析新技术机会和风险，分配责任、定义规程、衡量业绩 |
| ==业务与服务执行层== | 提供信息和数据服务，建设维护 IT 基础设施，响应 IT 需求 |

### 易混点

最高管理层偏“方向和价值”，执行管理层偏“目标和管理”，业务与服务执行层偏“交付和运行”。
"""),
    },
    {
        "point_id": "003",
        "section_id": "sec_01",
        "title": "IT治理与组织治理",
        "card_type": "concept",
        "difficulty": 1,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "组织治理"],
        "key_points": "- IT治理是**组织治理的重要组成部分**，不是单纯技术管理。",
        "mnemonics": "",
        "md": md("""
### 概述

IT治理属于组织治理的重要组成部分，目标是保证 IT 能支持并拓展组织战略和组织目标。

### 核心内容

IT治理把信息技术、信息资源、组织战略和组织目标连接起来，使 IT 决策、责任和评价有明确依据。

### 易混点

IT治理关注“治理结构和责任”，IT管理更偏“具体计划、建设、运行和控制”。
"""),
    },
    {
        "point_id": "004",
        "section_id": "sec_01",
        "title": "IT治理核心",
        "card_type": "concept",
        "difficulty": 2,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "责权利"],
        "key_points": "- 核心关键词：**IT定位、信息化建设、数字化转型、责权利划分**。",
        "mnemonics": "",
        "md": md("""
### 概述

IT治理的核心不是某个技术方案，而是围绕 IT 在组织中的定位，明确各方在信息化建设和数字化转型中的责任、权力与收益。

### 核心内容

IT治理的核心是关注 ==IT定位==，以及==信息化建设与数字化转型的责权利划分==。

### 易混点

看到“责权利划分、决策责任、谁输入、谁决策”时，通常是在考 IT治理。
"""),
    },
    {
        "point_id": "005",
        "section_id": "sec_01",
        "title": "五项关键决策",
        "card_type": "formula",
        "difficulty": 2,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "关键决策"],
        "key_points": "- 五项关键决策：**IT原则、IT架构、IT基础设施、业务应用需求、IT投资和优先顺序**。\n- 决策链：原则决定架构，架构决定基础设施，基础设施能力支撑业务应用。",
        "mnemonics": "记作：**原则架构建基础，应用投资排优先**。",
        "md": md("""
### 概述

有效的 IT治理必须关注一组会影响组织长期 IT 方向的关键决策。

### 核心内容

五项关键决策包括：==IT原则==、==IT架构==、==IT基础设施==、==业务应用需求==、==IT投资和优先顺序==。

### 决策关系

- IT原则驱动 IT整体架构的形成。
- IT整体架构决定基础设施。
- 基础设施能力决定基于业务需求的应用构建。
- IT投资和优先顺序应由 IT原则、整体架构、基础设施和应用需求共同驱动。

### 易混点

IT治理还要确定每项决策“谁负责输入、谁负责做出决策”，这是治理而不是单纯执行。
"""),
    },
    {
        "point_id": "006",
        "section_id": "sec_01",
        "title": "IT治理体系框架",
        "card_type": "formula",
        "difficulty": 2,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "治理框架"],
        "key_points": "- 框架组成：**战略目标、治理组织、治理机制、治理域、治理标准、绩效目标**。",
        "mnemonics": "",
        "md": md("""
### 概述

IT治理体系框架用于把治理目标、组织责任、运行机制和评价标准组织成闭环。

### 核心内容

IT治理体系框架包括：==IT战略目标==、==IT治理组织==、==IT治理机制==、==IT治理域==、==IT治理标准==和==IT绩效目标==。

### 易混点

“治理域”和“治理机制”不是同一个概念：治理域说明管什么，治理机制说明如何运转。
"""),
    },
    {
        "point_id": "007",
        "section_id": "sec_01",
        "title": "IT治理本质",
        "card_type": "concept",
        "difficulty": 1,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "业务价值"],
        "key_points": "- 本质两面：**实现IT业务价值** + **规避IT风险**。",
        "mnemonics": "",
        "md": md("""
### 概述

IT治理本质上处理的是 IT 对组织的价值和风险问题。

### 核心内容

IT治理本质上关系到：==实现IT的业务价值==，以及==IT风险的规避==。

### 易混点

只讲“技术先进”不等于治理有效；能否创造业务价值、控制风险，才是治理视角。
"""),
    },
    {
        "point_id": "008",
        "section_id": "sec_01",
        "title": "六项核心内容",
        "card_type": "formula",
        "difficulty": 2,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "核心内容"],
        "key_points": "- 六项核心内容：**组织职责、战略匹配、资源管理、价值交付、风险管理、绩效管理**。",
        "mnemonics": "记作：**职责配资源，价值控风险，看绩效**。",
        "md": md("""
### 概述

IT治理的核心内容回答“谁负责、和战略怎么对齐、资源怎么用、价值和风险如何评价”。

### 核心内容

IT治理的核心内容包括六个方面：==组织职责==、==战略匹配==、==资源管理==、==价值交付==、==风险管理==和==绩效管理==。

### 易混点

“风险管理”既是 IT治理目标之一，也是 IT治理核心内容之一；题目问法不同，答案集合不同。
"""),
    },
    {
        "point_id": "009",
        "section_id": "sec_01",
        "title": "治理机制原则",
        "card_type": "formula",
        "difficulty": 1,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "治理机制"],
        "key_points": "- 机制原则：**简单、透明、适合**。",
        "mnemonics": "记作：**简透适**。",
        "md": md("""
### 概述

IT治理机制要能被组织真正执行，而不是停留在复杂文档中。

### 核心内容

建立 IT治理机制的原则包括：==简单==、==透明==、==适合==。

### 易混点

“适合”强调与组织规模、行业、治理成熟度匹配，不是越复杂越好。
"""),
    },
    {
        "point_id": "010",
        "section_id": "sec_01",
        "title": "IT治理主要任务",
        "card_type": "formula",
        "difficulty": 2,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "治理任务"],
        "key_points": "- 主要任务：**全局统筹、价值导向、机制保障、创新发展、文化助推**。",
        "mnemonics": "",
        "md": md("""
### 概述

开展 IT治理活动，要同时关注组织全局、价值实现、制度机制、创新和文化。

### 核心内容

主要任务包括：==全局统筹==、==价值导向==、==机制保障==、==创新发展==、==文化助推==。

### 易混点

这组内容偏“治理活动怎么开展”，不要和“五项关键决策”混为一组。
"""),
    },
    {
        "point_id": "011",
        "section_id": "sec_01",
        "title": "典型治理标准",
        "card_type": "concept",
        "difficulty": 2,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "ITSS", "COBIT", "ISO38500"],
        "key_points": "- 典型标准/框架：**ITSS、COBIT、ISO/IEC 38500**。",
        "mnemonics": "",
        "md": md("""
### 概述

IT治理可以参考国内标准、国际框架和国际标准。

### 核心内容

比较典型的包括：我国信息技术服务标准库中的 ==ITSS IT治理系列标准==、信息和技术治理框架 ==COBIT==、IT治理国际标准 ==ISO/IEC 38500==。

### 易混点

ITSS偏国内标准体系，COBIT偏治理和管理目标框架，ISO/IEC 38500偏国际治理原则和任务。
"""),
    },
    {
        "point_id": "012",
        "section_id": "sec_01",
        "title": "IT治理标准化",
        "card_type": "concept",
        "difficulty": 2,
        "page": "30",
        "tags": ["信息系统治理", "IT治理", "标准化"],
        "key_points": "- 四个规范视角：**决策体系、责任归属、管理流程、内外评价**。",
        "mnemonics": "",
        "md": md("""
### 概述

我国 IT治理标准化研究强调用机制把 IT过程、IT资源、信息和组织战略目标连接起来。

### 核心内容

在 IT治理目标和边界确定后，IT治理围绕 ==决策体系==、==责任归属==、==管理流程==、==内外评价== 四个方面，规范和引导组织完成“做什么、如何做、做得怎么样、如何评价”。

### 易混点

这张卡关注“标准化研究如何规范治理”，不是某个具体标准的条款。
"""),
    },
    {
        "point_id": "013",
        "section_id": "sec_01",
        "title": "GB/T 34960.1用途",
        "card_type": "concept",
        "difficulty": 2,
        "page": "30",
        "tags": ["信息系统治理", "GB/T34960.1", "通用要求"],
        "key_points": "- 可用于：**建体系与自评、IT审计、研发选择评价方案、第三方评价**。",
        "mnemonics": "",
        "md": md("""
### 概述

GB/T 34960.1《信息技术服务 治理 第1部分：通用要求》给出 IT治理的通用要求。

### 核心内容

该标准可用于：

1. ==建立组织的IT治理体系，并实施自我评价==。
2. ==开展信息技术审计==。
3. 研发、选择和评价 IT治理相关的软件或解决方案。
4. 第三方对组织的 IT治理能力进行评价。

### 易混点

“通用要求”偏治理要求和评价依据，不是实施步骤指南。
"""),
    },
    {
        "point_id": "014",
        "section_id": "sec_01",
        "title": "GB/T 34960.1治理模型",
        "card_type": "concept",
        "difficulty": 2,
        "page": "30,31",
        "tags": ["信息系统治理", "GB/T34960.1", "治理模型"],
        "key_points": "- 模型包含：**内外部要求、治理主体、治理方法、管理体系**。",
        "mnemonics": "",
        "md": md("""
### 概述

GB/T 34960.1 定义的治理模型描述 IT治理由哪些要素构成。

### 核心内容

该标准定义的 IT治理模型包含：==治理的内外部要求==、==治理主体==、==治理方法==，以及信息技术及其应用的管理体系。

### 易混点

治理模型讲“治理要素”，治理框架讲“治理域划分”。
"""),
    },
    {
        "point_id": "015",
        "section_id": "sec_01",
        "title": "GB/T 34960.1三大治理域",
        "card_type": "comparison",
        "difficulty": 2,
        "page": "31",
        "tags": ["信息系统治理", "GB/T34960.1", "治理域"],
        "key_points": "- 三大治理域：**信息技术顶层设计、管理体系、资源**。",
        "mnemonics": "记作：**顶管资**。",
        "md": md("""
### 概述

GB/T 34960.1 定义的 IT治理框架包含三大治理域。

### 核心内容

| 治理域 | 关注内容 |
|:---|:---|
| ==信息技术顶层设计== | 信息技术战略，以及支撑战略的组织和架构 |
| ==管理体系== | 质量、项目、投资、服务、连续性、安全、风险、供方、资产等管理 |
| ==资源== | 基础设施、应用系统和数据 |

### 易混点

“顶层设计”看战略与架构，“管理体系”看管理活动，“资源”看基础设施、应用和数据。
"""),
    },
    {
        "point_id": "016",
        "section_id": "sec_01",
        "title": "顶层设计治理域",
        "card_type": "concept",
        "difficulty": 1,
        "page": "31",
        "tags": ["信息系统治理", "治理域", "顶层设计"],
        "key_points": "- 顶层设计治理域 = **战略 + 支撑战略的组织和架构**。",
        "mnemonics": "",
        "md": md("""
### 概述

顶层设计治理域关注 IT 在组织整体中的方向和结构安排。

### 核心内容

顶层设计治理域包含==信息技术的战略==，以及==支撑战略的组织和架构==。

### 易混点

题干出现“战略、组织、架构”时，优先对应顶层设计治理域。
"""),
    },
    {
        "point_id": "017",
        "section_id": "sec_01",
        "title": "管理体系治理域",
        "card_type": "concept",
        "difficulty": 2,
        "page": "31",
        "tags": ["信息系统治理", "治理域", "管理体系"],
        "key_points": "- 管理体系治理域覆盖各种管理：**质量、项目、投资、服务、连续性、安全、风险、供方、资产**等。",
        "mnemonics": "",
        "md": md("""
### 概述

管理体系治理域关注 IT相关管理活动是否成体系、可控制、可评价。

### 核心内容

管理体系治理域包含信息技术相关的==质量管理==、==项目管理==、==投资管理==、==服务管理==、==业务连续性管理==、==信息安全管理==、==风险管理==、==供方管理==、==资产管理==和其他管理。

### 易混点

题干出现一串“管理”词，通常不是资源域，而是管理体系治理域。
"""),
    },
    {
        "point_id": "018",
        "section_id": "sec_01",
        "title": "资源治理域",
        "card_type": "concept",
        "difficulty": 1,
        "page": "31",
        "tags": ["信息系统治理", "治理域", "资源"],
        "key_points": "- 资源治理域 = **基础设施、应用系统、数据**。",
        "mnemonics": "",
        "md": md("""
### 概述

资源治理域关注 IT 相关资源的配置、使用和治理。

### 核心内容

资源治理域包含信息技术相关的==基础设施==、==应用系统==和==数据==。

### 易混点

“基础设施、应用、数据”是资源，不是管理体系本身。
"""),
    },
    {
        "point_id": "019",
        "section_id": "sec_01",
        "title": "GB/T 34960.2用途",
        "card_type": "concept",
        "difficulty": 2,
        "page": "31",
        "tags": ["信息系统治理", "GB/T34960.2", "实施指南"],
        "key_points": "- 实施指南适用于：**建实施框架、内部实施、方案落地、第三方评价指导**。",
        "mnemonics": "",
        "md": md("""
### 概述

GB/T 34960.2《信息技术服务 治理 第2部分：实施指南》关注 IT治理如何实施落地。

### 核心内容

该标准适用于：

1. ==建立组织的IT治理实施框架，明确实施方法和过程==。
2. 组织内部开展 IT治理实施。
3. 指导 IT治理相关软件或解决方案实施落地。
4. 指导第三方开展 IT治理评价。

### 易混点

第1部分是“通用要求”，第2部分是“实施指南”；一个偏要求，一个偏落地。
"""),
    },
    {
        "point_id": "020",
        "section_id": "sec_01",
        "title": "IT治理实施框架",
        "card_type": "formula",
        "difficulty": 1,
        "page": "31",
        "tags": ["信息系统治理", "IT治理", "实施框架"],
        "key_points": "- 实施框架三部分：**实施环境、实施过程、治理域**。",
        "mnemonics": "记作：**环过域**。",
        "md": md("""
### 概述

IT治理实施框架描述治理从环境准备到过程实施再到治理域覆盖的整体安排。

### 核心内容

IT治理实施框架包括：==治理的实施环境==、==实施过程==和==治理域==。

### 易混点

不要把“实施框架三部分”和“GB/T 34960.1 三大治理域”混记；前者有实施环境和实施过程。
"""),
    },
    {
        "point_id": "021",
        "section_id": "sec_01",
        "title": "COBIT治理目标EDM",
        "card_type": "concept",
        "difficulty": 2,
        "page": "31",
        "tags": ["信息系统治理", "COBIT", "EDM"],
        "key_points": "- COBIT治理目标属于 **EDM：评估、指导和监控**。\n- 治理机构评估战略方案、指导高级管理层执行、监督实施。",
        "mnemonics": "EDM = **Evaluate、Direct、Monitor**。",
        "md": md("""
### 概述

COBIT 中治理目标被列入 EDM 领域，用来说明治理机构如何对战略进行治理。

### 核心内容

==EDM== 是 ==评估、指导和监控==。治理机构评估战略方案，指导高级管理层执行所选战略方案，并监督战略实施。

### 易混点

EDM 是治理目标领域，不是四个管理目标领域之一。
"""),
    },
    {
        "point_id": "022",
        "section_id": "sec_01",
        "title": "COBIT四个管理领域",
        "card_type": "comparison",
        "difficulty": 2,
        "page": "31",
        "tags": ["信息系统治理", "COBIT", "管理目标"],
        "key_points": "- 四个管理领域：**APO、BAI、DSS、MEA**。\n- APO偏规划组织，BAI偏构建采购实施，DSS偏交付支持，MEA偏监控评价。",
        "mnemonics": "",
        "md": md("""
### 概述

COBIT 中管理目标分为四个领域，分别覆盖规划、建设、运行和评价。

### 核心内容

| 领域 | 中文含义 | 关注点 |
|:---|:---|:---|
| ==APO== | 调整、规划和组织 | IT整体组织、战略和支持活动 |
| ==BAI== | 构建、采购和实施 | IT解决方案定义、采购、实施及与业务流程整合 |
| ==DSS== | 交付、服务和支持 | IT服务运营交付和支持，包括安全 |
| ==MEA== | 监控、评价和评估 | IT性能、内部控制目标和外部要求的一致性 |

### 易混点

治理目标看 EDM；管理目标看 APO、BAI、DSS、MEA。
"""),
    },
    {
        "point_id": "023",
        "section_id": "sec_01",
        "title": "治理目标与管理目标",
        "card_type": "comparison",
        "difficulty": 2,
        "page": "31",
        "tags": ["信息系统治理", "COBIT", "治理目标", "管理目标"],
        "key_points": "- **治理目标**对应治理流程，通常由董事会和执行管理层负责。\n- **管理目标**对应管理流程，在高级和中级管理层职责范围内。",
        "mnemonics": "",
        "md": md("""
### 概述

COBIT 区分治理目标和管理目标，是为了区分“治理层做什么”和“管理层做什么”。

### 核心内容

| 对比项 | 治理目标 | 管理目标 |
|:---|:---|:---|
| 关联流程 | ==治理流程== | ==管理流程== |
| 主要责任方 | 董事会和执行管理层 | 高级和中级管理层 |
| 典型领域 | EDM | APO、BAI、DSS、MEA |

### 易混点

看到“董事会、治理机构、评估指导监控”偏治理；看到“规划、构建、交付、监控评价”偏管理。
"""),
    },
    {
        "point_id": "024",
        "section_id": "sec_01",
        "title": "COBIT设计因素",
        "card_type": "concept",
        "difficulty": 3,
        "page": "31",
        "tags": ["信息系统治理", "COBIT", "设计因素"],
        "key_points": "- 设计因素用于定制治理系统，重点看**战略、目标、风险、合规、采购模式、技术采用、组织规模**等。",
        "mnemonics": "",
        "md": md("""
### 概述

COBIT 认为高效有效的 IT治理系统是创造价值的起点，而治理系统需要结合组织特点进行设计。

### 核心内容

COBIT 定义的 IT治理系统设计因素包括：==组织战略==、==组织目标==、==风险概况==、==IT相关问题==、威胁环境、合规性要求、IT角色、IT采购模式、IT实施方法、技术采用战略、组织规模和未来因素。

### 易混点

设计因素不是治理目标本身，而是用于“如何设计适合本组织的治理系统”。
"""),
    },
    {
        "point_id": "025",
        "section_id": "sec_01",
        "title": "COBIT设计流程",
        "card_type": "process",
        "difficulty": 2,
        "page": "31,32",
        "tags": ["信息系统治理", "COBIT", "设计流程"],
        "key_points": "- 四步：**了解环境和战略 → 确定初步范围 → 优化范围 → 最终确定设计**。",
        "mnemonics": "",
        "md": md("""
### 概述

COBIT 给出治理系统的建议设计流程，用于从组织背景出发确定治理系统设计。

### 核心内容

1. ==了解组织环境和战略==。
2. ==确定治理系统的初步范围==。
3. ==优化治理系统的范围==。
4. ==最终确定治理系统的设计==。

### 易混点

这组是“设计流程”，不要和 IT审计流程四阶段混淆。
"""),
    },
    {
        "point_id": "026",
        "section_id": "sec_01",
        "title": "ISO/IEC 38500意义",
        "card_type": "concept",
        "difficulty": 1,
        "page": "32",
        "tags": ["信息系统治理", "ISO38500", "IT治理标准"],
        "key_points": "- ISO/IEC 38500 是 IT治理国际标准，标志 IT治理进入更规范的发展阶段。",
        "mnemonics": "",
        "md": md("""
### 概述

ISO/IEC 38500 是 IT治理领域的重要国际标准。

### 核心内容

ISO/IEC 38500 的发布标志着 IT治理从概念探讨进入较规范的认识和发展阶段，也体现了信息化进入 ==IT治理时代==。

### 易混点

考试通常不要求展开标准背景，重点记住它是 IT治理国际标准，以及后续六项原则和三项任务。
"""),
    },
    {
        "point_id": "027",
        "section_id": "sec_01",
        "title": "ISO/IEC 38500六原则",
        "card_type": "formula",
        "difficulty": 2,
        "page": "32",
        "tags": ["信息系统治理", "ISO38500", "治理原则"],
        "key_points": "- 六原则：**责任、战略、收购、性能、一致性、人的行为**。",
        "mnemonics": "",
        "md": md("""
### 概述

ISO/IEC 38500 给出了治理信息技术时应遵循的六项原则。

### 核心内容

六项原则包括：==责任==、==战略==、==收购==、==性能==、==一致性==和==人的行为==。

### 易混点

“一致性”常指合规和符合要求；“人的行为”强调人的因素，不要漏掉。
"""),
    },
    {
        "point_id": "028",
        "section_id": "sec_01",
        "title": "ISO/IEC 38500三任务",
        "card_type": "formula",
        "difficulty": 1,
        "page": "32",
        "tags": ["信息系统治理", "ISO38500", "治理任务"],
        "key_points": "- 三项治理任务：**评估、指导、监督**。",
        "mnemonics": "与 COBIT EDM 语义接近：**评、指、监**。",
        "md": md("""
### 概述

ISO/IEC 38500 规定治理机构应通过三个主要任务来治理 IT。

### 核心内容

治理机构应通过 ==评估==、==指导==、==监督== 三个主要任务来治理 IT。

### 易混点

COBIT EDM 常译为“评估、指导和监控”；ISO/IEC 38500 此处常见表述为“评估、指导、监督”。
"""),
    },
    {
        "point_id": "029",
        "section_id": "sec_02",
        "title": "IT审计目的",
        "card_type": "concept",
        "difficulty": 1,
        "page": "32",
        "tags": ["信息系统治理", "IT审计", "审计目的"],
        "key_points": "- IT审计目的：了解总体状况、评价目标实现、识别评估风险、提出改进建议。",
        "mnemonics": "",
        "md": md("""
### 概述

IT审计通过独立、系统的审查评价，帮助组织确认 IT 系统和 IT 活动是否支持组织目标。

### 核心内容

IT审计的目的是了解组织 IT系统与 IT活动的总体状况，对组织是否实现 IT目标进行审查和评价，==识别与评估IT风险==，提出评价意见和改进建议，促进组织实现 IT目标。

### 易混点

IT审计不是直接替组织整改系统，而是审查、评价、识别风险并提出建议。
"""),
    },
    {
        "point_id": "030",
        "section_id": "sec_02",
        "title": "组织IT目标",
        "card_type": "formula",
        "difficulty": 2,
        "page": "32",
        "tags": ["信息系统治理", "IT审计", "IT目标"],
        "key_points": "- IT目标四类：**战略一致、资产与数据安全完整可靠有效、系统安全可靠有效、合规**。",
        "mnemonics": "",
        "md": md("""
### 概述

IT审计要围绕组织的 IT目标展开，判断 IT 是否真正支撑业务并满足安全、有效和合规要求。

### 核心内容

组织的 IT目标主要包括：

1. ==IT战略与业务战略保持一致==。
2. 保护信息资产安全，保证数据完整、可靠、有效。
3. 提高信息系统的安全性、可靠性及有效性。
4. 合理保证信息系统及其运用符合法律、法规及标准要求。

### 易混点

“数据完整可靠有效”和“系统安全可靠有效”分别指数据和系统，不要混作同一项。
"""),
    },
    {
        "point_id": "031",
        "section_id": "sec_02",
        "title": "IT审计范围",
        "card_type": "comparison",
        "difficulty": 2,
        "page": "32",
        "tags": ["信息系统治理", "IT审计", "审计范围"],
        "key_points": "- 审计范围包括：**总体范围、组织范围、物理范围、逻辑范围、其他相关事项**。",
        "mnemonics": "",
        "md": md("""
### 概述

确定 IT审计范围，是为了明确审计要看哪些组织、系统、边界和事项。

### 核心内容

| 范围 | 含义 |
|:---|:---|
| ==总体范围== | 根据审计目的和审计成本确定 |
| ==组织范围== | 明确涉及的组织机构、主要流程、活动及人员 |
| ==物理范围== | 明确具体物理地点与边界 |
| ==逻辑范围== | 明确涉及的信息系统和逻辑边界 |
| ==其他相关事项== | 与审计目的相关的其他范围约束 |

### 易混点

物理范围看地点和边界，逻辑范围看系统和逻辑边界。
"""),
    },
    {
        "point_id": "032",
        "section_id": "sec_02",
        "title": "IT审计人员要求",
        "card_type": "concept",
        "difficulty": 2,
        "page": "32",
        "tags": ["信息系统治理", "IT审计", "审计人员"],
        "key_points": "- 要求关键词：**职业道德、知识、技能、资格与经验、专业胜任能力、外部专家服务**。",
        "mnemonics": "",
        "md": md("""
### 概述

IT审计既涉及审计方法，也涉及信息技术知识，因此对审计人员有综合要求。

### 核心内容

根据 GB/T 34690.4《信息技术服务 治理 第4部分：审计导则》，IT审计人员要求包括==职业道德==、==知识==、==技能==、==资格与经验==、==专业胜任能力==以及利用外部专家服务等方面。

### 易混点

IT审计人员不是只懂审计即可，也需要具备与信息技术服务治理相关的知识和技能。
"""),
    },
    {
        "point_id": "033",
        "section_id": "sec_02",
        "title": "IT审计风险",
        "card_type": "comparison",
        "difficulty": 3,
        "page": "32",
        "tags": ["信息系统治理", "IT审计", "审计风险"],
        "key_points": "- 风险类型：**固有风险、控制风险、检查风险、总体审计风险**。\n- 固有风险和控制风险主要由被审计对象决定；检查风险与审计程序和审计人员有关。",
        "mnemonics": "",
        "md": md("""
### 概述

IT审计风险用于描述审计过程中可能无法发现重大问题或无法形成恰当结论的风险。

### 核心内容

IT审计风险主要包括==固有风险==、==控制风险==、==检查风险==和==总体审计风险==。

| 类型 | 学习抓手 |
|:---|:---|
| 固有风险 | IT活动本身容易导致重大错误的风险，审计人员只能评估，不能控制 |
| 控制风险 | 内部控制不能及时预防或发现重大错误的风险，属于内部控制范畴 |
| 检查风险 | 通过预定审计程序未能发现重大错误的风险，受审计规范、人员和技术影响 |
| 总体审计风险 | 针对单个控制目标产生的各类审计风险总和 |

### 易混点

固有风险看“活动本身”，控制风险看“内部控制是否有效”，检查风险看“审计程序是否发现问题”。
"""),
    },
    {
        "point_id": "034",
        "section_id": "sec_02",
        "title": "常用审计方法",
        "card_type": "comparison",
        "difficulty": 2,
        "page": "33",
        "tags": ["信息系统治理", "IT审计", "审计方法"],
        "key_points": "- 方法六类：**访谈、调查、检查、观察、测试、程序代码检查**。",
        "mnemonics": "",
        "md": md("""
### 概述

IT审计方法用于收集证据、理解现状和验证控制或系统是否有效。

### 核心内容

常用审计方法包括：==访谈法==、==调查法==、==检查法==、==观察法==、==测试法==和==程序代码检查法==。

| 方法 | 学习抓手 |
|:---|:---|
| 访谈法 | 面对面交谈，了解被审计对象信息 |
| 调查法 | 通过书面或口头回答问题收集资料并分析 |
| 检查法 | 审查记录、文件或实物资产 |
| 观察法 | 到现场察看，证实审计事项 |
| 测试法 | 使用测试数据或测试过程评估程序质量 |
| 程序代码检查法 | 逐条检查程序指令的合法性、完整性和逻辑正确性 |

### 易混点

检查法看资料和实物，观察法看现场过程，测试法看程序或控制运行结果。
"""),
    },
    {
        "point_id": "035",
        "section_id": "sec_02",
        "title": "常用IT审计技术",
        "card_type": "comparison",
        "difficulty": 2,
        "page": "34",
        "tags": ["信息系统治理", "IT审计", "审计技术"],
        "key_points": "- 技术四类：**风险评估、审计抽样、计算机辅助审计、大数据审计**。\n- CAAT 常见工具包括通用审计软件、测试数据、实用工具软件、专家系统等。",
        "mnemonics": "",
        "md": md("""
### 概述

IT审计技术是审计人员在风险识别、样本测试、计算机辅助分析和大数据分析中使用的方法工具。

### 核心内容

| 技术 | 学习抓手 |
|:---|:---|
| ==风险评估技术== | 包括风险识别、风险分析、风险评价和风险应对 |
| ==审计抽样技术== | 从总体中选取样本测试，并推断总体特征 |
| ==计算机辅助审计技术（CAAT）== | 以计算机为工具执行审计程序和任务 |
| ==大数据审计技术== | 运用大数据方法进行跨层级、跨系统、跨部门、跨业务分析 |

### 易混点

审计抽样解决“不能全量查”的问题；CAAT强调用计算机辅助审计；大数据审计强调海量、多源、跨域分析。
"""),
    },
    {
        "point_id": "036",
        "section_id": "sec_02",
        "title": "审计证据",
        "card_type": "concept",
        "difficulty": 1,
        "page": "34",
        "tags": ["信息系统治理", "IT审计", "审计证据"],
        "key_points": "- 审计证据是形成**审计结论**的基础，也是审计意见的支柱。",
        "mnemonics": "",
        "md": md("""
### 概述

审计证据是审计人员形成审计结论的基础。

### 核心内容

审计证据是审计机构和审计人员获取的，用于确定所审计实体或数据是否遵循既定标准或目标、形成审计结论的证明材料。

### 易混点

审计证据不是审计报告本身，而是支撑审计结论和审计意见的材料。
"""),
    },
    {
        "point_id": "037",
        "section_id": "sec_02",
        "title": "审计证据五特性",
        "card_type": "comparison",
        "difficulty": 2,
        "page": "34",
        "tags": ["信息系统治理", "IT审计", "审计证据"],
        "key_points": "- 五特性：**充分性、客观性、相关性、可靠性、合法性**。\n- 充分性偏数量，相关性偏联系，可靠性偏可信程度。",
        "mnemonics": "记作：**充客相可靠法**。",
        "md": md("""
### 概述

审计证据必须满足一定质量要求，才能支撑审计结论。

### 核心内容

| 特性 | 含义 |
|:---|:---|
| ==充分性== | 证据数量足以支持审计结论，主要与样本量有关 |
| ==客观性== | 证据是客观存在的事实材料 |
| ==相关性== | 证据与审计事项之间有实质性联系 |
| ==可靠性== | 证据能反映和证实客观活动特征，受类型、来源和取证方式影响 |
| ==合法性== | 证据符合法定种类，并依法定程序取得 |

### 易混点

充分性问“够不够”，相关性问“有没有关系”，可靠性问“信不信得过”。
"""),
    },
    {
        "point_id": "038",
        "section_id": "sec_02",
        "title": "审计工作底稿",
        "card_type": "concept",
        "difficulty": 1,
        "page": "34",
        "tags": ["信息系统治理", "IT审计", "工作底稿"],
        "key_points": "- 工作底稿记录计划、程序、证据和结论，是**审计证据的载体**。",
        "mnemonics": "",
        "md": md("""
### 概述

审计工作底稿记录审计过程，是审计质量控制和复核的重要依据。

### 核心内容

审计工作底稿是审计人员对制订的审计计划、实施的审计程序、获取的相关审计证据以及得出的审计结论做出的记录。它是==审计证据的载体==，形成于审计过程，也反映整个审计过程。

### 易混点

工作底稿既记录过程，也沉淀资料；不是只在审计结束后才补写的报告附件。
"""),
    },
    {
        "point_id": "039",
        "section_id": "sec_02",
        "title": "工作底稿作用",
        "card_type": "formula",
        "difficulty": 2,
        "page": "34",
        "tags": ["信息系统治理", "IT审计", "工作底稿"],
        "key_points": "- 作用四类：**审计意见依据、人员考核依据、质量控制基础、未来备查参考**。",
        "mnemonics": "",
        "md": md("""
### 概述

审计工作底稿的作用不只在当前项目，也影响质量控制和后续审计。

### 核心内容

审计工作底稿的作用包括：

1. 形成审计结论、发表审计意见的直接依据。
2. 评价考核审计人员的主要依据。
3. 审计质量控制与监督的基础。
4. 对未来审计业务具有参考备查作用。

### 易混点

“直接依据”对应审计结论和审计意见；“基础”对应质量控制与监督。
"""),
    },
    {
        "point_id": "040",
        "section_id": "sec_02",
        "title": "工作底稿分类",
        "card_type": "comparison",
        "difficulty": 2,
        "page": "35",
        "tags": ["信息系统治理", "IT审计", "工作底稿"],
        "key_points": "- 三类：**综合类、业务类、备查类**。\n- 综合类用于规划控制总结，业务类用于执行具体程序，备查类用于持续备查。",
        "mnemonics": "",
        "md": md("""
### 概述

审计工作底稿按用途和形成阶段可分为三类。

### 核心内容

| 类型 | 学习抓手 |
|:---|:---|
| ==综合类工作底稿== | 计划阶段和报告阶段形成，用于规划、控制、总结审计工作并发表审计意见 |
| ==业务类工作底稿== | 实施阶段执行具体审计程序形成，如内部控制调查表、流程图、项目明细表 |
| ==备查类工作底稿== | 对审计工作仅具有备查作用，随被审计单位情况变化不断更新 |

### 易混点

业务类底稿更贴近具体审计项目；备查类底稿偏长期资料和背景资料。
"""),
    },
    {
        "point_id": "041",
        "section_id": "sec_02",
        "title": "底稿三级复核",
        "card_type": "formula",
        "difficulty": 1,
        "page": "35",
        "tags": ["信息系统治理", "IT审计", "三级复核"],
        "key_points": "- 三级复核人：**审计机构负责人、部门负责人、项目负责人（或项目经理）**。",
        "mnemonics": "从大到小记：**机构、部门、项目**。",
        "md": md("""
### 概述

三级复核制度用于保证审计工作底稿质量。

### 核心内容

审计工作底稿三级复核制度，是指以==审计机构负责人==、==部门负责人==和==项目负责人（或项目经理）==为复核人。

### 易混点

三级复核考的是复核人的层级，不是审计流程四阶段。
"""),
    },
    {
        "point_id": "042",
        "section_id": "sec_02",
        "title": "底稿查阅例外",
        "card_type": "concept",
        "difficulty": 2,
        "page": "35",
        "tags": ["信息系统治理", "IT审计", "工作底稿"],
        "key_points": "- 不属于泄密的两种查阅：**司法/国家机关依法查阅**，**审计协会或委派单位执业检查**。",
        "mnemonics": "",
        "md": md("""
### 概述

审计工作底稿通常涉及保密，但法律和行业检查场景存在例外。

### 核心内容

下列两种情况需要查阅审计工作底稿的，不属于泄密情形：

1. ==法院、检察院及国家其他部门依法查阅==，并按规定办理必要手续。
2. ==审计协会或其委派单位对审计机构执业情况进行检查==。

### 易混点

关键不是“任何人都能查阅”，而是依法、按规定、为执业检查或法定职责查阅。
"""),
    },
    {
        "point_id": "043",
        "section_id": "sec_02",
        "title": "审计档案管理",
        "card_type": "concept",
        "difficulty": 1,
        "page": "35",
        "tags": ["信息系统治理", "IT审计", "审计档案"],
        "key_points": "- 底稿归档后交由档案管理部门管理，并确保**安全、完整**。",
        "mnemonics": "",
        "md": md("""
### 概述

审计工作底稿按标准归档后，就成为审计档案的重要组成部分。

### 核心内容

审计工作底稿按照一定标准归入审计档案后，应交由档案管理部门进行管理，并确保审计档案的==安全==、==完整==。

### 易混点

归档管理强调安全和完整，不是由项目组随意长期保存。
"""),
    },
    {
        "point_id": "044",
        "section_id": "sec_02",
        "title": "审计流程四阶段",
        "card_type": "process",
        "difficulty": 3,
        "page": "35",
        "tags": ["信息系统治理", "IT审计", "审计流程"],
        "key_points": "- 四阶段：**审计准备、审计实施、审计终结、后续审计**。\n- 后续审计关注整改措施是否落实并取得预期效果。",
        "mnemonics": "记作：**准备、实施、终结、后续**。",
        "md": md("""
### 概述

IT审计流程描述审计项目从计划到整改跟踪的完整过程。

### 核心内容

审计流程一般分为==审计准备==、==审计实施==、==审计终结==及==后续审计==四个阶段。

| 阶段 | 主要工作 |
|:---|:---|
| 审计准备 | 明确审计目的及任务，组建项目组，搜集信息，编制审计计划 |
| 审计实施 | 深入调查并调整计划，了解并初步评估 IT内部控制，进行符合性测试和实质性测试 |
| 审计终结 | 整理复核底稿，整理证据，评价控制目标实现，判断并报告发现，沟通结果，出具报告并归档 |
| 后续审计 | 检查被审计单位是否采取纠正措施，并确认是否取得预期效果 |

### 易混点

后续审计发生在审计报告发出后，且可不必遵守审计流程的每一过程和要求。
"""),
    },
    {
        "point_id": "045",
        "section_id": "sec_02",
        "title": "IT审计业务类型",
        "card_type": "comparison",
        "difficulty": 2,
        "page": "35,36",
        "tags": ["信息系统治理", "IT审计", "审计业务"],
        "key_points": "- 两类：**IT内部控制审计**和**IT专项审计**。\n- 内控审计分组织层面、一般控制、应用控制；专项审计针对特殊风险或需求。",
        "mnemonics": "",
        "md": md("""
### 概述

IT审计业务和服务通常按审计目标和范围分为两类。

### 核心内容

| 类型 | 学习抓手 |
|:---|:---|
| ==IT内部控制审计== | 包括组织层面 IT控制审计、IT一般控制审计及应用控制审计 |
| ==IT专项审计== | 根据当前特殊风险或需求开展，范围为 IT综合审计的某一个或几个部分 |

### 易混点

内部控制审计关注控制体系；专项审计关注特定风险、特定需求或特定审计范围。
"""),
    },
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_highlight(text: str) -> bool:
    return "==" in text


def estimated_read_seconds(text: str) -> int:
    return max(30, min(180, round(len(text) / 6)))


def build_card_json(card: dict, sort_no: int) -> dict:
    point_id = card["point_id"]
    section_id = card["section_id"]
    stem = f"{CHAPTER_ID}_{section_id}_{point_id}"
    md_text = card["md"]
    return {
        "point_id": point_id,
        "subject_id": SUBJECT_ID,
        "chapter_id": CHAPTER_ID,
        "section_id": section_id,
        "title": card["title"],
        "card_type": card["card_type"],
        "difficulty": card["difficulty"],
        "estimated_read_seconds": estimated_read_seconds(md_text),
        "has_key_content": has_highlight(md_text),
        "is_free": True,
        "sort_no": sort_no,
        "content_file": f"{stem}.md",
        "content_md_path": f"subjects/{SUBJECT_ID}/chapters/{CHAPTER_ID}/cards/{stem}.md",
        "tags": card["tags"],
        "key_points": card.get("key_points", ""),
        "mnemonics": card.get("mnemonics", ""),
        "warnings": "第三章已按 PDF 第30-36页与知识卡片规范重制；受 OCR 来源限制，仍建议上线前抽样核对原 PDF。",
        "prerequisite_point_ids": [f"{sort_no - 1:03d}"] if sort_no > 1 else [],
        "related_point_ids": [],
        "related_question_ids": [],
        "source": "2026新版高项三色笔记（信息系统项目管理师）",
        "source_type": "exam_note",
        "source_refs": [
            {
                "source_id": "pdf_2026_tricolor_high",
                "page_label": card["page"],
            }
        ],
        "author": "Codex curated from color OCR",
        "reviewer": "待人工复核",
        "review_status": "ai_draft",
        "created_at": "2026-05-13T00:00:00+08:00",
        "updated_at": BUILD_TIME,
        "version": 3,
        "schema_version": 2,
    }


def rebuild_chapter_cards() -> dict[str, int]:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    keep_files: set[str] = set()
    section_counts = {"sec_01": 0, "sec_02": 0}

    for sort_no, card in enumerate(CARDS, start=1):
        stem = f"{CHAPTER_ID}_{card['section_id']}_{card['point_id']}"
        json_path = CARDS_DIR / f"{stem}.json"
        md_path = CARDS_DIR / f"{stem}.md"
        md_path.write_text(card["md"], encoding="utf-8")
        write_json(json_path, build_card_json(card, sort_no))
        keep_files.update({json_path.name, md_path.name})
        section_counts[card["section_id"]] += 1

    for path in sorted(CARDS_DIR.glob("ch_03_sec_02_0[4-6][0-9].*")):
        if path.name not in keep_files:
            path.unlink()
    for path in sorted(CARDS_DIR.glob("ch_03_sec_02_062.*")):
        if path.name not in keep_files:
            path.unlink()

    return section_counts


def update_counts(section_counts: dict[str, int]) -> None:
    card_count = len(CARDS)

    chapter_meta_path = CHAPTER_ROOT / "chapter_meta.json"
    chapter_meta = read_json(chapter_meta_path)
    chapter_meta["description"] = "IT治理与IT审计，由 PDF 第30-36页整理为移动端知识卡片。"
    chapter_meta["card_count"] = card_count
    for section in chapter_meta["sections"]:
        section["card_count"] = section_counts.get(section["section_id"], 0)
        if section["section_id"] == "sec_01":
            section["description"] = "IT治理目标、层次、关键决策、治理域、ITSS、COBIT、ISO/IEC 38500。"
        elif section["section_id"] == "sec_02":
            section["description"] = "IT审计目标、范围、风险、方法、技术、证据、工作底稿和审计流程。"
    write_json(chapter_meta_path, chapter_meta)

    subject_path = PUBLIC_ROOT / "subjects" / SUBJECT_ID / "subject_index.json"
    subject = read_json(subject_path)
    for chapter in subject["chapters"]:
        if chapter["chapter_id"] == CHAPTER_ID:
            chapter["card_count"] = card_count
            break
    subject["updated_at"] = BUILD_TIME
    write_json(subject_path, subject)

    manifest_path = PUBLIC_ROOT / "manifest.json"
    manifest = read_json(manifest_path)
    manifest["content_version"] = CONTENT_VERSION
    manifest["generated_at"] = BUILD_TIME
    manifest["updated_at"] = BUILD_TIME
    total = 0
    for chapter in manifest.get("chapters", []):
        if chapter["chapter_id"] == CHAPTER_ID:
            chapter["card_count"] = card_count
        total += chapter.get("card_count", 0)
    manifest["card_count"] = total
    write_json(manifest_path, manifest)


def rebuild_file_index() -> None:
    entries = []
    for path in sorted(PUBLIC_ROOT.rglob("*")):
        if path.is_file() and path.name != "file_index.json":
            entries.append(
                {
                    "path": path.relative_to(PUBLIC_ROOT).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    write_json(
        PUBLIC_ROOT / "file_index.json",
        {
            "package_id": "atomq_public_content",
            "version": CONTENT_VERSION,
            "file_count": len(entries),
            "files": entries,
        },
    )


def main() -> None:
    if len(CARDS) != 45:
        raise RuntimeError(f"expected 45 cards, got {len(CARDS)}")
    section_counts = rebuild_chapter_cards()
    update_counts(section_counts)
    rebuild_file_index()
    print(f"rebuilt {CHAPTER_ID}: cards={len(CARDS)} section_counts={section_counts}")


if __name__ == "__main__":
    main()
