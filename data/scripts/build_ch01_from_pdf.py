#!/usr/bin/env python3
"""Build the refreshed Chapter 1 content package.

The source PDF has a custom text encoding in the full file. The first split PDF
in the same folder contains a usable ToUnicode map, so this builder records both
paths and uses the split file as the extraction source for Chapter 1.
"""

from __future__ import annotations

import json
import re
import shutil
import zlib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = ROOT / "content_package"
SUBJECT_ID = "high_itpmp"
CHAPTER_ID = "ch_01"
SOURCE_ID = "pdf_2026_tricolor_high"
FULL_PDF = Path("/Users/leiwang/Downloads/三色笔记/2026新版高项三色笔记（信息系统项目管理师）.pdf")
SPLIT_PDF = Path("/Users/leiwang/Downloads/三色笔记/拆分/2026新版高项三色笔记（信息系统项目管理师）（拖移项目 01）.pdf")
BUILD_TIME = "2026-05-11T00:00:00+08:00"


@dataclass(frozen=True)
class Card:
    point_id: str
    section_id: str
    title: str
    card_type: str
    difficulty: int
    estimated_read_seconds: int
    tags: list[str]
    key_points: str
    mnemonics: str
    prerequisites: list[str]
    related: list[str]
    source_pages: list[str]
    markdown: str
    is_free: bool = True


SECTIONS = [
    {
        "section_id": "sec_01",
        "title": "信息与信息化",
        "sort_no": 1,
        "description": "信息定义、信息质量、信息系统、软件与信息系统生命周期、信息化内涵与国家信息化体系。",
    },
    {
        "section_id": "sec_02",
        "title": "现代化基础设施",
        "sort_no": 2,
        "description": "新型基础设施、工业互联网、车联网的关键概念和体系结构。",
    },
    {
        "section_id": "sec_03",
        "title": "现代化创新发展",
        "sort_no": 3,
        "description": "农业现代化、两化融合、智能制造和消费互联网。",
    },
    {
        "section_id": "sec_04",
        "title": "数字中国",
        "sort_no": 4,
        "description": "数字中国、数字经济、数字政府、智慧城市、数字乡村和数字生活。",
    },
]


CARDS = [
    Card(
        "kp_ch01_001",
        "sec_01_01",
        "信息的定义",
        "definition",
        1,
        90,
        ["信息", "确定性", "物质", "能量"],
        "信息是物质、能量及其属性的标示集合；学习时抓住“确定性的增加”。",
        "信息不是物质能量本身，而是让不确定变确定。",
        [],
        ["kp_ch01_002", "kp_ch01_003"],
        ["第1页"],
        """### 概述

信息可以理解为对事物属性和状态的表达。考试中常用的表述是：信息是==物质、能量及其属性的标示的集合==，也是==确定性的增加==。

### 考试抓手

- 信息不是物质本身，也不是能量本身
- 信息依附于载体，但价值来自它降低不确定性的能力
- 遇到“确定性增加”“消除不确定性”一类说法，通常指向信息的本质

:::key
信息 = 属性标示 + 确定性增加。
:::
""",
    ),
    Card(
        "kp_ch01_002",
        "sec_01_01",
        "维纳与香农的信息观点",
        "comparison",
        1,
        90,
        ["维纳", "香农", "控制论", "信息论"],
        "维纳强调信息独立于物质和能量；香农强调信息用于消除不确定性。",
        "维纳说“非物非能”，香农说“消除不确定”。",
        ["kp_ch01_001"],
        ["kp_ch01_001"],
        ["第1页"],
        """### 概述

维纳和香农是信息相关考点里最容易被混淆的一组人物。

<!-- render:native caption:维纳与香农对比 -->
| 人物 | 身份 | 高频观点 |
|:---|:---|:---|
| ==维纳== | 控制论创始人 | 信息既不是物质，也不是能量 |
| ==香农== | 信息论奠基者 | 信息是能够消除不确定性的东西 |

:::warning
题干出现“消除不确定性”时，优先联想到香农；出现“不是物质，也不是能量”时，优先联想到维纳。
:::
""",
    ),
    Card(
        "kp_ch01_003",
        "sec_01_01",
        "信息的 11 个特征",
        "concept",
        2,
        180,
        ["信息特征", "客观性", "依附性", "转化性"],
        "信息特征共 11 个，重点记住客观、普遍、无限、动态、相对、依附、变换、传递、层次、系统、转化。",
        "客普无动相，依变传层系转。",
        ["kp_ch01_001"],
        ["kp_ch01_004"],
        ["第1页"],
        """### 概述

信息的特征属于枚举型考点，通常考“属于/不属于”或给出场景让你判断特征。

<!-- render:native caption:信息的 11 个特征 -->
| 特征 | 速记理解 |
|:---|:---|
| ==客观性== | 信息反映客观事物 |
| ==普遍性== | 信息无处不在 |
| ==无限性== | 信息可持续产生和积累 |
| ==动态性== | 信息会随时间和状态变化 |
| ==相对性== | 同一信息对不同主体价值不同 |
| ==依附性== | 信息需要依附载体 |
| ==变换性== | 信息可加工、转换形式 |
| ==传递性== | 信息可跨时间、空间传递 |
| ==层次性== | 信息可按管理层级和抽象程度划分 |
| ==系统性== | 信息之间存在结构化联系 |
| ==转化性== | 信息可转化为知识、能力或生产力 |

:::tip
背诵口诀：客普无动相，依变传层系转。
:::
""",
    ),
    Card(
        "kp_ch01_004",
        "sec_01_01",
        "信息的质量属性",
        "concept",
        2,
        150,
        ["信息质量", "安全性", "及时性", "可靠性"],
        "信息质量属性包括精确、完整、可靠、及时、经济、可验证、安全；金融信息尤其重安全，经济社会信息尤其重及时。",
        "精完可及，经可安。",
        ["kp_ch01_003"],
        [],
        ["第1页"],
        """### 概述

信息质量属性用于判断一条信息“好不好用、值不值得信、是否适合当前场景”。

<!-- render:native caption:信息质量属性 -->
| 属性 | 判断问题 |
|:---|:---|
| ==精确性== | 是否准确反映事实 |
| ==完整性== | 是否缺少必要信息 |
| ==可靠性== | 来源是否可信 |
| ==及时性== | 是否在需要时可用 |
| ==经济性== | 获取和使用成本是否合理 |
| ==可验证性== | 是否能被证实或证伪 |
| ==安全性== | 是否避免未授权访问、篡改或泄露 |

:::key
金融信息突出==安全性==；经济与社会信息突出==及时性==。
:::
""",
    ),
    Card(
        "kp_ch01_005",
        "sec_01_01",
        "信息系统的概念与三要素",
        "concept",
        2,
        150,
        ["信息系统", "管理模型", "信息处理模型", "系统实现条件"],
        "信息系统通过输入数据、加工处理、产生信息；显著特点是面向管理和支持生产。",
        "信息系统三件套：管模型、理信息、靠条件。",
        ["kp_ch01_001"],
        ["kp_ch01_006", "kp_ch01_008"],
        ["第1页"],
        """### 概述

信息系统是把数据输入系统，经过加工处理后输出有用信息的系统。它的显著特点是==面向管理和支持生产==。

### 三个核心组成

- ==管理模型==：服务对象领域的知识，以及分析、处理该领域问题的模型
- ==信息处理模型==：系统处理信息的结构和方法
- ==系统实现条件==：计算机技术、通信技术、人员，以及对这些资源的控制与融合

:::key
常见概括：信息系统 = 人 + 技术 + 资源。
:::
""",
    ),
    Card(
        "kp_ch01_006",
        "sec_01_01",
        "信息系统组成部件",
        "concept",
        1,
        120,
        ["硬件", "软件", "数据库", "网络", "规程"],
        "信息系统组成包括硬件、软件、数据库、网络、存储设备、感知设备、外设、人员和规程。",
        "硬软数网存，感外人规程。",
        ["kp_ch01_005"],
        [],
        ["第1页"],
        """### 概述

信息系统由技术、资源和人协同构成，具体部件可以按下列清单记忆。

1. ==硬件==
2. ==软件==
3. ==数据库==
4. ==网络==
5. ==存储设备==
6. ==感知设备==
7. ==外设==
8. ==人员==
9. ==规程==

:::tip
口诀：硬软数网存，感外人规程。
:::
""",
    ),
    Card(
        "kp_ch01_007",
        "sec_01_01",
        "软件生命周期",
        "process",
        1,
        120,
        ["软件生命周期", "需求分析", "设计", "测试", "维护"],
        "软件生命周期依次覆盖可行性分析与项目开发计划、需求分析、概要设计、详细设计、编码、测试、维护。",
        "可需概详编测维。",
        ["kp_ch01_005"],
        ["kp_ch01_008"],
        ["第1页"],
        """### 概述

软件生命周期描述软件从立项到退役的完整过程。

<!-- render:native caption:软件生命周期 -->
| 顺序 | 阶段 |
|:---|:---|
| 1 | ==可行性分析与项目开发计划== |
| 2 | ==需求分析== |
| 3 | ==概要设计== |
| 4 | ==详细设计== |
| 5 | ==编码== |
| 6 | ==测试== |
| 7 | ==维护== |

:::tip
口诀：可需概详编测维。
:::
""",
    ),
    Card(
        "kp_ch01_008",
        "sec_01_01",
        "信息系统生命周期",
        "process",
        2,
        150,
        ["信息系统生命周期", "系统规划", "系统分析", "系统设计", "系统实施"],
        "信息系统生命周期可简化为规划、分析、设计、实施、运行维护五个阶段。",
        "规分设实运。",
        ["kp_ch01_007"],
        [],
        ["第1页"],
        """### 概述

信息系统生命周期常与软件生命周期对照考查。它更强调系统层面的规划、建设和运行。

<!-- render:native caption:信息系统生命周期 -->
| 阶段 | 对应活动 |
|:---|:---|
| ==系统规划== | 可行性分析与项目开发计划 |
| ==系统分析== | 需求分析 |
| ==系统设计== | 概要设计、详细设计 |
| ==系统实施== | 编码、测试、部署 |
| ==系统运行和维护== | 运行、优化、维护 |

:::warning
软件生命周期和信息系统生命周期名称相近，考试常用“系统规划/系统分析/系统设计”来提示信息系统生命周期。
:::
""",
    ),
    Card(
        "kp_ch01_009",
        "sec_01_01",
        "信息化核心与内涵",
        "concept",
        2,
        180,
        ["信息化", "信息网络体系", "信息产业基础", "效用积累"],
        "信息化核心是充分应用基于信息技术的先进生产工具，提高社会生产力，并推动生产关系和上层建筑改革。",
        "网产环效：网络体系、产业基础、运行环境、效用积累。",
        ["kp_ch01_001"],
        ["kp_ch01_010"],
        ["第1页"],
        """### 概述

信息化不是简单“上系统”，而是全社会在经济和社会领域充分应用基于信息技术的先进生产工具，提升生产力，并推动生产关系和上层建筑调整。

### 四个内涵

- ==信息网络体系==：信息资源、各类信息系统、公用通信网络平台
- ==信息产业基础==：信息科学技术研发、信息装备制造、信息咨询服务
- ==社会运行环境==：现代工农业、管理体制、政策法律、规章制度、文化教育和道德观念
- ==效用积累过程==：劳动者素质、国家现代化水平和人民生活质量持续提高

:::key
信息化的落点是综合实力、文明程度和生活质量的全面提升。
:::
""",
    ),
    Card(
        "kp_ch01_010",
        "sec_01_01",
        "国家信息化体系",
        "concept",
        2,
        120,
        ["国家信息化体系", "信息资源", "信息网络", "标准规范"],
        "国家信息化体系有 6 个要素：应用、资源、网络、技术和产业、人才、政策法规和标准规范。",
        "用资网技人政标。",
        ["kp_ch01_009"],
        [],
        ["第1页"],
        """### 概述

国家信息化体系是支撑国家层面信息化建设的总体框架。

1. ==信息技术应用==
2. ==信息资源==
3. ==信息网络==
4. ==信息技术和产业==
5. ==信息化人才==
6. ==信息化政策法规和标准规范==

:::tip
口诀：用资网技人政标。
:::
""",
    ),
    Card(
        "kp_ch01_011",
        "sec_01_01",
        "信息化趋势与数字化发展方向",
        "concept",
        3,
        180,
        ["信息化趋势", "数字中国", "十四五规划"],
        "信息化呈现产品、产业、社会生活、国民经济四类趋势；当前进入加快数字化发展、建设数字中国阶段。",
        "产品嵌信息，产业用技术，生活上平台，经济成大流动。",
        ["kp_ch01_009"],
        ["kp_ch01_021"],
        ["第2页"],
        """### 概述

信息化趋势可从产品、产业、社会生活和国民经济四个层面理解。

<!-- render:native caption:信息化趋势 -->
| 趋势 | 说明 |
|:---|:---|
| ==产品信息化== | 产品中信息比重提高，智能化元器件增多 |
| ==产业信息化== | 农业、工业、服务业广泛利用信息技术 |
| ==社会生活信息化== | 市场、教育、政务、日常生活等建立网络平台 |
| ==国民经济信息化== | 金融、贸易、投资、生产、流通等形成统一信息流 |

:::key
新阶段关键词：加快数字化发展，建设数字中国。
:::
""",
    ),
    Card(
        "kp_ch01_012",
        "sec_01_02",
        "新型基础设施建设",
        "concept",
        2,
        180,
        ["新基建", "信息基础设施", "融合基础设施", "创新基础设施"],
        "新型基础设施以信息网络为基础，提供数字转型、智能升级、融合创新服务。",
        "新基建三类：信息、融合、创新。",
        [],
        ["kp_ch01_013", "kp_ch01_016"],
        ["第2页"],
        """### 概述

新型基础设施以新发展理念为引领，以技术创新为驱动，以信息网络为基础，服务数字转型、智能升级和融合创新。

<!-- render:native caption:新型基础设施分类 -->
| 类型 | 典型内容 |
|:---|:---|
| ==信息基础设施== | 5G、物联网、工业互联网、卫星互联网、人工智能、云计算、区块链、数据中心、智能计算中心 |
| ==融合基础设施== | 智能交通基础设施、智慧能源基础设施等 |
| ==创新基础设施== | 重大科技基础设施、科教基础设施、产业技术创新基础设施 |

:::warning
题目出现“支撑传统基础设施转型升级”时，多半指融合基础设施。
:::
""",
    ),
    Card(
        "kp_ch01_013",
        "sec_01_02",
        "工业互联网定义与定位",
        "definition",
        2,
        150,
        ["工业互联网", "工业数字化", "实体经济"],
        "工业互联网是新一代信息通信技术与工业经济深度融合，不是互联网在工业中的简单套用。",
        "工业互联网：网络为基础，平台为中枢，数据为要素，安全为保障。",
        ["kp_ch01_012"],
        ["kp_ch01_014"],
        ["第3页"],
        """### 概述

工业互联网是新一代信息通信技术与工业经济深度融合形成的新型基础设施、应用模式和产业生态。

### 四个定位

- ==网络为基础==
- ==平台为中枢==
- ==数据为要素==
- ==安全为保障==

:::key
工业互联网不是“把互联网搬进工厂”，而是支撑工业数字化、网络化、智能化转型的基础设施和应用模式。
:::
""",
    ),
    Card(
        "kp_ch01_014",
        "sec_01_02",
        "工业互联网平台体系",
        "concept",
        3,
        210,
        ["工业互联网平台", "边缘层", "IaaS", "PaaS", "SaaS"],
        "工业互联网平台体系包括边缘层、IaaS、PaaS、SaaS，主要作用是数据汇聚、建模分析、知识复用、应用创新。",
        "边 I P S 四层；汇模复创四用。",
        ["kp_ch01_013"],
        [],
        ["第3页"],
        """### 概述

工业互联网平台相当于工业互联网的“操作系统”，向下连接设备和数据，向上支撑应用创新。

### 四层平台体系

1. ==边缘层==
2. ==IaaS==
3. ==PaaS==
4. ==SaaS==

### 四个主要作用

- ==数据汇聚==
- ==建模分析==
- ==知识复用==
- ==应用创新==

:::warning
工业互联网数据具有重要性、专业性、复杂性；安全保障常围绕监测预警、应急响应、检测评估、功能测试展开。
:::
""",
    ),
    Card(
        "kp_ch01_015",
        "sec_01_02",
        "车联网端管云体系",
        "concept",
        2,
        180,
        ["车联网", "智能网联汽车", "端管云"],
        "车联网是端、管、云三层体系，支持车与云、车与车、车与路、车与人、车内设备互联。",
        "端采集，管连接，云汇聚。",
        ["kp_ch01_012"],
        [],
        ["第4页"],
        """### 概述

车联网是新一代网络通信技术与汽车、电子、道路交通运输等领域深度融合的新兴产业形态。

<!-- render:native caption:车联网端管云 -->
| 层级 | 作用 |
|:---|:---|
| ==端系统== | 车辆传感器和泛在通信终端，采集车辆与环境信息 |
| ==管系统== | 实现车与车、车与路、车与网、车与人的互联互通 |
| ==云系统== | 汇聚车辆运行信息，支撑计算、调度、监控、管理与应用 |

### 五类连接

车与云平台、车与车、车与路、车与人、车内设备。
""",
    ),
    Card(
        "kp_ch01_016",
        "sec_01_03",
        "农业现代化与数字乡村基础",
        "concept",
        2,
        150,
        ["农业现代化", "农业信息化", "乡村振兴", "智慧农业"],
        "农业现代化用现代装备、科学技术、管理方法和文化知识改造农业；农业信息化是重要技术手段。",
        "装备、技术、管理、素质四路并进。",
        ["kp_ch01_012"],
        ["kp_ch01_025"],
        ["第5页"],
        """### 概述

农业现代化是用现代工业装备农业、用现代科学技术改造农业、用现代管理方法管理农业、用现代科学文化知识提高农民素质的过程。

### 数字化方向

- 农村宽带、5G、移动物联网与城市同步规划建设
- 推动农业生产加工和农村基础设施数字化、智能化升级
- 建立农业农村大数据体系
- 推动物联网、大数据、人工智能、区块链与农业生产经营融合
- 建设数字田园、数字灌区和智慧农牧渔场
""",
    ),
    Card(
        "kp_ch01_017",
        "sec_01_03",
        "两化融合",
        "concept",
        2,
        150,
        ["两化融合", "信息化", "工业化", "新型工业化"],
        "两化融合是信息化和工业化高层次深度结合，以信息化带动工业化，以工业化促进信息化。",
        "技产业务产业，四处融合。",
        ["kp_ch01_009"],
        [],
        ["第5页"],
        """### 概述

两化融合是信息化和工业化的高层次深度结合，目标是走新型工业化道路。

<!-- render:native caption:两化融合领域 -->
| 融合领域 | 说明 |
|:---|:---|
| ==技术融合== | 工业技术与信息技术融合，产生新技术 |
| ==产品融合== | 电子信息技术或产品渗透到工业产品中 |
| ==业务融合== | 信息技术应用于研发、生产、经营、营销等环节 |
| ==产业衍生== | 催生工业电子、工业软件、工业信息服务业等新产业 |

:::key
两化融合的核心是信息化支撑，追求可持续发展模式。
:::
""",
    ),
    Card(
        "kp_ch01_018",
        "sec_01_03",
        "智能制造与成熟度模型",
        "concept",
        3,
        210,
        ["智能制造", "GB/T39116", "成熟度模型"],
        "智能制造能力成熟度分为规划级、规范级、集成级、优化级、引领级。",
        "规规范，集优化，引领协同。",
        ["kp_ch01_017"],
        [],
        ["第5页", "第6页"],
        """### 概述

智能制造是由智能机器和人类专家共同组成的人机一体化智能系统。智能制造建设是一项持续性的系统工程。

<!-- render:native caption:智能制造成熟度等级 -->
| 等级 | 名称 | 核心含义 |
|:---|:---|:---|
| 1 | ==规划级== | 开始规划基础和条件，对核心业务活动流程化管理 |
| 2 | ==规范级== | 用自动化、信息化手段改造装备和业务活动 |
| 3 | ==集成级== | 装备、系统集成，跨业务活动数据共享 |
| 4 | ==优化级== | 通过数据挖掘形成知识和模型，实现预测与优化 |
| 5 | ==引领级== | 基于模型持续驱动优化创新，实现产业链协同 |

:::warning
“规划级”不是成熟度很高，而是刚开始规划；“引领级”才是最高等级。
:::
""",
    ),
    Card(
        "kp_ch01_019",
        "sec_01_03",
        "消费互联网",
        "definition",
        1,
        120,
        ["消费互联网", "媒体属性", "产业属性", "个人虚拟化"],
        "消费互联网以消费者为服务中心，本质是个人虚拟化，增强个人生活消费体验。",
        "消费互联网看个人体验，产业互联网看生产效率。",
        ["kp_ch01_009"],
        [],
        ["第6页"],
        """### 概述

消费互联网以消费者为服务中心，改善个人用户在阅读、出行、娱乐、生活等场景中的体验。

### 两类属性

- ==媒体属性==：自媒体、社会媒体、资讯门户等
- ==产业属性==：在线旅行、生活服务、电商等

:::key
消费互联网的本质是个人虚拟化，目标是增强个人生活消费体验。
:::
""",
    ),
    Card(
        "kp_ch01_020",
        "sec_01_04",
        "数字中国主线",
        "concept",
        2,
        120,
        ["数字中国", "数字经济", "数字社会", "数字政府"],
        "数字中国强调激活数据要素潜能，推进网络强国建设，以数字化转型驱动生产、生活和治理方式变革。",
        "数经、数社、数政三条主线。",
        ["kp_ch01_011"],
        ["kp_ch01_021", "kp_ch01_023"],
        ["第6页"],
        """### 概述

数字中国建设的主线是迎接数字时代、激活数据要素潜能、推进网络强国建设，并加快建设数字经济、数字社会、数字政府。

:::key
数字化转型的影响对象：生产方式、生活方式、治理方式。
:::
""",
    ),
    Card(
        "kp_ch01_021",
        "sec_01_04",
        "数字经济构成",
        "concept",
        3,
        180,
        ["数字经济", "数字产业化", "产业数字化", "数据价值化"],
        "数字经济从产业构成看包括数字产业化和产业数字化；从整体构成看包括数字产业化、产业数字化、数字化治理、数据价值化。",
        "两分法：产业化、产业数字化；四分法再加治理和价值化。",
        ["kp_ch01_020"],
        ["kp_ch01_022"],
        ["第6页"],
        """### 概述

数字经济是以数字技术与实体经济融合驱动产业转型和经济创新的新技术经济范式。

### 两种拆法

- 从产业构成看：==数字产业化==、==产业数字化==
- 从整体构成看：==数字产业化==、==产业数字化==、==数字化治理==、==数据价值化==

:::warning
题目问“产业构成”通常答两项；问“整体构成”通常答四项。
:::
""",
    ),
    Card(
        "kp_ch01_022",
        "sec_01_04",
        "数字产业化、产业数字化与数据价值化",
        "comparison",
        3,
        210,
        ["数字产业化", "产业数字化", "数据价值化"],
        "数字产业化强调数字技术形成产业；产业数字化强调传统产业被数字技术改造；数据价值化强调数据成为可流通、可治理、可增值的资源要素。",
        "数字变产业，产业变数字，数据变价值。",
        ["kp_ch01_021"],
        [],
        ["第6页", "第7页"],
        """### 概述

数字经济相关概念很容易混淆，建议用“谁被数字化、谁形成产业”来区分。

<!-- render:native caption:数字经济关键概念对比 -->
| 概念 | 判断方式 |
|:---|:---|
| ==数字产业化== | 数字技术本身形成产业，如电子信息制造、软件、互联网服务 |
| ==产业数字化== | 传统产业应用数字技术提升效率和模式 |
| ==数据价值化== | 数据被采集、治理、流通、开发后成为价值资源 |
| ==数字化治理== | 运用数字技术提升治理能力和治理效率 |

:::tip
口诀：数字变产业，产业变数字，数据变价值。
:::
""",
    ),
    Card(
        "kp_ch01_023",
        "sec_01_04",
        "数字政府",
        "concept",
        2,
        150,
        ["数字政府", "政务服务", "治理能力"],
        "数字政府强调以数字技术推进政府治理流程再造、模式优化和履职能力提升。",
        "服务协同，治理增效。",
        ["kp_ch01_020"],
        ["kp_ch01_024"],
        ["第7页", "第8页"],
        """### 概述

数字政府是数字中国建设的重要组成部分，重点在于用数字技术推动政府治理能力现代化。

### 高频理解

- 政务服务从线下分散转向线上协同
- 数据共享支撑跨部门、跨层级业务联动
- 数字技术帮助政府提升精准治理、协同治理和智能决策能力

:::key
数字政府不是简单“政务上网”，核心是治理流程、治理模式和治理能力的数字化转型。
:::
""",
    ),
    Card(
        "kp_ch01_024",
        "sec_01_04",
        "智慧城市能力与成熟度",
        "concept",
        3,
        240,
        ["智慧城市", "数据治理", "城市孪生", "成熟度"],
        "智慧城市核心能力包括数据治理、城市孪生、边际决策、多元融合、态势感知；成熟度从规划级到引领级共 5 级。",
        "数城边多态；规管协优引。",
        ["kp_ch01_023"],
        [],
        ["第8页", "第9页"],
        """### 概述

智慧城市通过信息通信技术整合城市管理系统，促进信息资源共享和业务协同，使城市管理与服务更加智慧化。

### 五大能力要素

1. ==数据治理==
2. ==城市孪生==
3. ==边际决策==
4. ==多元融合==
5. ==态势感知==

### 五级成熟度

规划级、管理级、协同级、优化级、引领级。

:::tip
能力口诀：数城边多态。成熟度口诀：规管协优引。
:::
""",
    ),
    Card(
        "kp_ch01_025",
        "sec_01_04",
        "数字乡村与数字生活",
        "concept",
        2,
        150,
        ["数字乡村", "数字生活", "乡村振兴"],
        "数字乡村是数字中国的重要内容；数字生活体现生活工具、生活方式、生活内容的数字化。",
        "乡村数字化，生活三数字。",
        ["kp_ch01_016", "kp_ch01_020"],
        [],
        ["第9页"],
        """### 概述

数字乡村是在农业农村经济社会发展中应用网络化、信息化和数字化能力，是乡村振兴的战略方向，也是建设数字中国的重要内容。

### 数字生活三类体现

- ==生活工具数字化==：信息技术和产品成为重要生活工具
- ==生活方式数字化==：工作、学习、消费、交往、娱乐方式数字化
- ==生活内容数字化==：工作、学习、消费和娱乐内容本身呈现数字化特征

:::key
数字乡村偏农业农村现代化；数字生活偏个人与家庭生活方式变化。
:::
""",
    ),
]


QUESTIONS = [
    {
        "question_id": "q_ch01_001",
        "subject_id": SUBJECT_ID,
        "chapter_id": CHAPTER_ID,
        "knowledge_point_ids": [{"point_id": "kp_ch01_002", "is_primary": True}],
        "difficulty": 1,
        "year": None,
        "stem": "“信息是能够用来消除不确定性的东西”这一观点通常对应哪位学者？",
        "options": [
            {"key": "A", "text": "维纳"},
            {"key": "B", "text": "香农"},
            {"key": "C", "text": "德鲁克"},
            {"key": "D", "text": "戴明"},
        ],
        "answer": "B",
        "analysis": "香农从信息论角度强调信息用于消除不确定性；维纳强调信息既不是物质，也不是能量。",
        "is_free": True,
        "domain_tags": ["信息化发展", "信息定义"],
    },
    {
        "question_id": "q_ch01_002",
        "subject_id": SUBJECT_ID,
        "chapter_id": CHAPTER_ID,
        "knowledge_point_ids": [{"point_id": "kp_ch01_004", "is_primary": True}],
        "difficulty": 2,
        "year": None,
        "stem": "对于金融信息而言，通常最应优先关注的信息质量属性是？",
        "options": [
            {"key": "A", "text": "安全性"},
            {"key": "B", "text": "经济性"},
            {"key": "C", "text": "层次性"},
            {"key": "D", "text": "变换性"},
        ],
        "answer": "A",
        "analysis": "金融信息对泄露、篡改和未授权访问高度敏感，因此安全性是关键质量属性。",
        "is_free": True,
        "domain_tags": ["信息质量", "信息化发展"],
    },
    {
        "question_id": "q_ch01_003",
        "subject_id": SUBJECT_ID,
        "chapter_id": CHAPTER_ID,
        "knowledge_point_ids": [{"point_id": "kp_ch01_012", "is_primary": True}],
        "difficulty": 2,
        "year": None,
        "stem": "智能交通基础设施、智慧能源基础设施更接近新型基础设施中的哪一类？",
        "options": [
            {"key": "A", "text": "信息基础设施"},
            {"key": "B", "text": "融合基础设施"},
            {"key": "C", "text": "创新基础设施"},
            {"key": "D", "text": "传统基础设施"},
        ],
        "answer": "B",
        "analysis": "融合基础设施强调互联网、大数据、人工智能等技术对传统基础设施的转型升级。",
        "is_free": True,
        "domain_tags": ["新型基础设施", "现代化基础设施"],
    },
    {
        "question_id": "q_ch01_004",
        "subject_id": SUBJECT_ID,
        "chapter_id": CHAPTER_ID,
        "knowledge_point_ids": [{"point_id": "kp_ch01_014", "is_primary": True}],
        "difficulty": 3,
        "year": None,
        "stem": "工业互联网平台体系通常包括边缘层、IaaS、PaaS 和哪一层？",
        "options": [
            {"key": "A", "text": "SaaS"},
            {"key": "B", "text": "TCP"},
            {"key": "C", "text": "BIOS"},
            {"key": "D", "text": "ERP"},
        ],
        "answer": "A",
        "analysis": "工业互联网平台体系包括边缘层、IaaS、PaaS、SaaS 四个层级。",
        "is_free": False,
        "domain_tags": ["工业互联网", "现代化基础设施"],
    },
    {
        "question_id": "q_ch01_005",
        "subject_id": SUBJECT_ID,
        "chapter_id": CHAPTER_ID,
        "knowledge_point_ids": [{"point_id": "kp_ch01_018", "is_primary": True}],
        "difficulty": 2,
        "year": None,
        "stem": "智能制造能力成熟度模型的最高等级是？",
        "options": [
            {"key": "A", "text": "规划级"},
            {"key": "B", "text": "规范级"},
            {"key": "C", "text": "优化级"},
            {"key": "D", "text": "引领级"},
        ],
        "answer": "D",
        "analysis": "智能制造能力成熟度从规划级、规范级、集成级、优化级到引领级，最高为引领级。",
        "is_free": False,
        "domain_tags": ["智能制造", "现代化创新发展"],
    },
    {
        "question_id": "q_ch01_006",
        "subject_id": SUBJECT_ID,
        "chapter_id": CHAPTER_ID,
        "knowledge_point_ids": [{"point_id": "kp_ch01_021", "is_primary": True}],
        "difficulty": 3,
        "year": None,
        "stem": "从数字经济的产业构成看，数字经济主要包括哪两部分？",
        "options": [
            {"key": "A", "text": "数字政府和数字社会"},
            {"key": "B", "text": "数字产业化和产业数字化"},
            {"key": "C", "text": "数据治理和城市孪生"},
            {"key": "D", "text": "信息网络和信息资源"},
        ],
        "answer": "B",
        "analysis": "从产业构成看，数字经济包括数字产业化和产业数字化；整体构成才扩展到数字化治理和数据价值化。",
        "is_free": False,
        "domain_tags": ["数字经济", "数字中国"],
    },
    {
        "question_id": "q_ch01_007",
        "subject_id": SUBJECT_ID,
        "chapter_id": CHAPTER_ID,
        "knowledge_point_ids": [{"point_id": "kp_ch01_024", "is_primary": True}],
        "difficulty": 2,
        "year": None,
        "stem": "智慧城市能力要素中，用于描述现实世界与信息世界互动融合的是？",
        "options": [
            {"key": "A", "text": "城市孪生"},
            {"key": "B", "text": "消费互联网"},
            {"key": "C", "text": "边缘层"},
            {"key": "D", "text": "产业衍生"},
        ],
        "answer": "A",
        "analysis": "城市孪生围绕现实世界与信息世界互动融合进行能力构建。",
        "is_free": False,
        "domain_tags": ["智慧城市", "数字中国"],
    },
]


def get_stream(obj: bytes) -> bytes | None:
    match = re.search(rb"stream\r?\n(.*?)endstream", obj, re.DOTALL)
    if not match:
        return None
    raw = match.group(1).rstrip()
    if b"/FlateDecode" in obj:
        try:
            return zlib.decompress(raw)
        except zlib.error:
            return raw
    return raw


def parse_cmap(stream_data: bytes) -> dict[str, str]:
    text = stream_data.decode("latin-1", errors="replace")
    mapping: dict[str, str] = {}
    for _, ranges in re.findall(r"(\d+) beginbfrange\s*(.*?)\s*endbfrange", text, re.DOTALL):
        for start_h, end_h, uni_h in re.findall(
            r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", ranges
        ):
            start, end, uni = int(start_h, 16), int(end_h, 16), int(uni_h, 16)
            for offset in range(end - start + 1):
                mapping[f"{start + offset:04X}"] = chr(uni + offset)
    for _, chars in re.findall(r"(\d+) beginbfchar\s*(.*?)\s*endbfchar", text, re.DOTALL):
        for code_h, uni_h in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", chars):
            mapping[code_h.upper()] = chr(int(uni_h, 16))
    return mapping


def extract_pdf_text(path: Path) -> str:
    data = path.read_bytes()
    object_pattern = re.compile(rb"(\d+ \d+ obj.*?endobj)", re.DOTALL)
    objects = {tuple(m.group(1).split(b" ")[:2]): m.group(1) for m in object_pattern.finditer(data)}

    def find_obj(ref: str) -> bytes | None:
        parts = ref.split()
        return objects.get((parts[0].encode(), parts[1].encode()))

    font_maps: dict[str, dict[str, str]] = {}
    for obj in objects.values():
        for short_h, ref_h in re.findall(rb"/(C\d+)\s+(\d+ \d+ R)", obj):
            short = short_h.decode()
            if short in font_maps:
                continue
            font_obj = find_obj(ref_h.decode())
            if not font_obj:
                continue
            unicode_ref = re.search(rb"/ToUnicode\s+(\d+ \d+ R)", font_obj)
            if not unicode_ref:
                continue
            cmap_obj = find_obj(unicode_ref.group(1).decode())
            if not cmap_obj:
                continue
            stream = get_stream(cmap_obj)
            if stream:
                mapping = parse_cmap(stream)
                if mapping:
                    font_maps[short] = mapping

    pages: list[str] = []
    for obj in objects.values():
        stream = get_stream(obj)
        if not stream:
            continue
        blocks = re.findall(rb"BT(.*?)ET", stream, re.DOTALL)
        if len(blocks) < 10:
            continue
        lines: list[str] = []
        for block in blocks:
            font_match = re.search(rb"/(C\d+)\s+", block)
            font = font_match.group(1).decode() if font_match else None
            mapping = font_maps.get(font or "", {})
            text_match = re.search(rb"<([0-9A-Fa-f]+)>\s*Tj", block)
            if not text_match:
                continue
            hex_text = text_match.group(1).decode().upper()
            glyphs = [hex_text[i : i + 4] for i in range(0, len(hex_text), 4)]
            text = "".join(mapping.get(glyph, "") for glyph in glyphs).strip()
            if text:
                lines.append(text)
        if lines:
            pages.append("".join(lines))
    return "\n\n".join(pages)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def point_id(value: str) -> str:
    return value.split("_")[-1]


def section_id(value: str) -> str:
    parts = value.split("_")
    return f"sec_{parts[-1]}" if len(parts) >= 2 else value


def card_file_stem(card: Card) -> str:
    return f"{CHAPTER_ID}_{section_id(card.section_id)}_{point_id(card.point_id)}"


def point_ids(values: list[str]) -> list[str]:
    return [point_id(value) for value in values]


def card_meta(card: Card, sort_no: int, question_ids: list[str]) -> dict[str, object]:
    return {
        "point_id": point_id(card.point_id),
        "subject_id": SUBJECT_ID,
        "chapter_id": CHAPTER_ID,
        "section_id": section_id(card.section_id),
        "title": card.title,
        "card_type": card.card_type,
        "difficulty": card.difficulty,
        "estimated_read_seconds": card.estimated_read_seconds,
        "has_key_content": "==" in card.markdown,
        "is_free": card.is_free,
        "sort_no": sort_no,
        "content_file": f"{card_file_stem(card)}.md",
        "tags": card.tags,
        "key_points": card.key_points,
        "mnemonics": card.mnemonics,
        "prerequisite_point_ids": point_ids(card.prerequisites),
        "related_point_ids": point_ids(card.related),
        "related_question_ids": question_ids,
        "source": "2026新版高项三色笔记（信息系统项目管理师）",
        "source_type": "exam_note",
        "source_refs": [{"source_id": SOURCE_ID, "page_label": page} for page in card.source_pages],
        "author": "Codex 内容整理",
        "reviewer": "待人工复核",
        "review_status": "ai_draft",
        "created_at": BUILD_TIME,
        "updated_at": BUILD_TIME,
        "version": 1,
        "schema_version": 2,
    }


def build() -> None:
    if CONTENT_ROOT.exists():
        shutil.rmtree(CONTENT_ROOT)

    raw_text = extract_pdf_text(SPLIT_PDF) if SPLIT_PDF.exists() else ""
    source_summary = {
        "source_id": SOURCE_ID,
        "full_pdf_path": str(FULL_PDF),
        "extraction_pdf_path": str(SPLIT_PDF),
        "chapter_id": CHAPTER_ID,
        "raw_extract_chars": len(raw_text),
        "raw_extract_pages_detected": raw_text.count("第") if raw_text else 0,
        "notes": [
            "Full PDF text layer uses a custom encoding that is not directly extractable by pypdf.",
            "The split PDF contains ToUnicode maps and was used only as the Chapter 1 extraction source.",
            "Generated cards are structured, edited study notes rather than verbatim PDF transcription.",
        ],
    }

    write_json(ROOT / "sources" / "source_manifest.json", source_summary)

    section_counts = {section["section_id"]: 0 for section in SECTIONS}
    question_by_point: dict[str, list[str]] = {}
    for question in QUESTIONS:
        for ref in question["knowledge_point_ids"]:
            ref["point_id"] = point_id(ref["point_id"])
            question_by_point.setdefault(ref["point_id"], []).append(question["question_id"])

    cards_dir = CONTENT_ROOT / "subjects" / SUBJECT_ID / "chapters" / CHAPTER_ID / "cards"
    for index, card in enumerate(CARDS, start=1):
        normalized_section_id = section_id(card.section_id)
        normalized_point_id = point_id(card.point_id)
        section_counts[normalized_section_id] += 1
        stem = card_file_stem(card)
        write_json(cards_dir / f"{stem}.json", card_meta(card, index, question_by_point.get(normalized_point_id, [])))
        write_text(cards_dir / f"{stem}.md", card.markdown)

    subject_index = {
        "subject_id": SUBJECT_ID,
        "subject_name": "高级-信息系统项目管理师",
        "exam_version": "2026",
        "chapters": [
            {
                "chapter_id": CHAPTER_ID,
                "title": "信息化发展",
                "sort_no": 1,
                "card_count": len(CARDS),
                "question_count": len(QUESTIONS),
            }
        ],
        "schema_version": 2,
    }

    chapter_meta = {
        "chapter_id": CHAPTER_ID,
        "subject_id": SUBJECT_ID,
        "title": "信息化发展",
        "description": "围绕信息与信息化、现代化基础设施、现代化创新发展和数字中国展开，是软考高项信息化基础知识的入口章节。",
        "sort_no": 1,
        "sections": [{**section, "card_count": section_counts[section["section_id"]]} for section in SECTIONS],
        "schema_version": 2,
    }

    package_manifest = {
        "package_id": "atomq_high_level_2026_ch01_preview",
        "subject_id": SUBJECT_ID,
        "content_version": "2026.05.ch01-preview.1",
        "generated_at": BUILD_TIME,
        "source_ids": [SOURCE_ID],
        "chapters": [
            {
                "chapter_id": CHAPTER_ID,
                "title": "信息化发展",
                "card_count": len(CARDS),
                "question_count": len(QUESTIONS),
            }
        ],
        "storage_policy": {
            "static_content": "CDN or app bundle fallback",
            "dynamic_user_data": "SQLite locally, Supabase/Postgres for cloud sync",
        },
        "schema_version": 2,
    }

    questions_path = CONTENT_ROOT / "subjects" / SUBJECT_ID / "questions" / "ch_01_questions.json"
    write_json(CONTENT_ROOT / "manifest.json", package_manifest)
    write_json(CONTENT_ROOT / "subjects" / SUBJECT_ID / "subject_index.json", subject_index)
    write_json(CONTENT_ROOT / "subjects" / SUBJECT_ID / "chapters" / CHAPTER_ID / "chapter_meta.json", chapter_meta)
    write_json(questions_path, QUESTIONS)

    write_text(
        ROOT / "local_store" / "schema.sql",
        """
-- Local dynamic store schema. Static JSON/Markdown content is intentionally not stored here.
CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  login_status TEXT NOT NULL CHECK (login_status IN ('guest', 'login', 'vip')),
  subject_id TEXT NOT NULL DEFAULT 'high_itpmp',
  exam_date TEXT,
  weekly_days INTEGER CHECK (weekly_days BETWEEN 0 AND 7),
  daily_minutes INTEGER CHECK (daily_minutes > 0),
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_records (
  record_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  target_type TEXT NOT NULL CHECK (target_type IN ('point', 'question', 'paper')),
  target_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('not_start', 'doing', 'done')),
  last_position TEXT,
  answer_time_ms INTEGER,
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS wrong_book (
  wrong_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  wrong_count INTEGER NOT NULL DEFAULT 1,
  right_streak INTEGER NOT NULL DEFAULT 0,
  priority TEXT NOT NULL CHECK (priority IN ('high', 'normal', 'archived')),
  last_wrong_at TEXT NOT NULL,
  next_review_at TEXT,
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS mastery_scores (
  user_id TEXT NOT NULL,
  subject_id TEXT NOT NULL DEFAULT 'high_itpmp',
  chapter_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  point_id TEXT NOT NULL,
  score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, subject_id, chapter_id, section_id, point_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS daily_tasks (
  task_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  task_date TEXT NOT NULL,
  task_type TEXT NOT NULL CHECK (task_type IN ('learn', 'practice', 'wrong_review')),
  target_id TEXT,
  target_count INTEGER NOT NULL DEFAULT 0,
  completed_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN ('pending', 'doing', 'done', 'skipped')),
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_records_user ON user_records(user_id);
CREATE INDEX IF NOT EXISTS idx_wrong_book_user ON wrong_book(user_id);
CREATE INDEX IF NOT EXISTS idx_wrong_book_question ON wrong_book(question_id);
CREATE INDEX IF NOT EXISTS idx_daily_tasks_user_date ON daily_tasks(user_id, task_date);
""",
    )

    write_text(
        ROOT / "README.md",
        """
# AtomQ Data

当前目录采用新结构：

- `.old/`：旧脚本、旧样例、旧 SQLite，保留作参考但不再作为可发布数据源。
- `content_package/`：可下发的静态内容包，包含科目索引、章节元数据、知识卡片 JSON/Markdown、章节题目 JSON。
- `local_store/`：客户端本地动态库 schema，存用户学习记录、错题、掌握度和每日任务。
- `sources/`：内容来源与抽取说明。
- `scripts/`：内容构建与校验脚本。

静态内容继续使用 JSON + Markdown；动态用户数据进入 SQLite。后续同步到云端时，`content_package` 走 CDN/Storage，`local_store` 对应表走 Supabase/Postgres。
""",
    )


if __name__ == "__main__":
    build()
    print(f"Built {len(CARDS)} cards and {len(QUESTIONS)} questions for {CHAPTER_ID}.")
