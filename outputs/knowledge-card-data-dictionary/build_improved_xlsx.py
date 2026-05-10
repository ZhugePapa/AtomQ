#!/usr/bin/env python3
"""生成改进版数据字典 xlsx（纯 stdlib，无需 openpyxl）"""

import zipfile, os, shutil, xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape
from tempfile import TemporaryDirectory
from datetime import datetime

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '软考刷题App_知识卡片数据字典.xlsx')
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '软考刷题App_知识卡片数据字典_V1.4.xlsx')

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
NS_R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
ET.register_namespace('', NS)
ET.register_namespace('r', NS_R)
ns = {'x': NS}
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

# ── XML builders ──────────────────────────────────────────────

def xrow(r, cells, row_ht=None):
    """Build a <row> element. cells = [(col_letter, style_id, value), ...]"""
    attrs = {'r': str(r)}
    if row_ht:
        attrs['ht'] = str(row_ht)
        attrs['customHeight'] = '1'
    el = ET.Element(f'{{{NS}}}row', attrs)
    for col, s, v in cells:
        c = ET.SubElement(el, f'{{{NS}}}c', {'r': f'{col}{r}', 's': str(s), 't': 'str'})
        cv = ET.SubElement(c, f'{{{NS}}}v')
        cv.text = xml_escape(str(v))
    return el

def sheet_xml(cols_el, rows_els, merged_cells=None):
    """Build complete worksheet XML."""
    ws = ET.Element(f'{{{NS}}}worksheet')
    ET.SubElement(ws, f'{{{NS}}}sheetFormatPr', {'defaultRowHeight': '15'})
    ws.append(cols_el)
    sd = ET.SubElement(ws, f'{{{NS}}}sheetData')
    for row_el in rows_els:
        sd.append(row_el)
    if merged_cells:
        mc = ET.SubElement(ws, f'{{{NS}}}mergeCells', {'count': str(len(merged_cells))})
        for m in merged_cells:
            ET.SubElement(mc, f'{{{NS}}}mergeCell', {'ref': m})
    return ET.tostring(ws, encoding='unicode', xml_declaration=True)

# ── Sheet 1: 评估 (updated) ───────────────────────────────────

def build_sheet1():
    """评估 sheet — 更新评估结论，反映改进后的状态"""
    rows = []

    # Row 1: Title (merged A1:D1)
    rows.append((1, [
        ('A', 6, '软考刷题 App 知识卡片数据方案评估'),
        ('B', 6, '软考刷题 App 知识卡片数据方案评估'),
        ('C', 6, '软考刷题 App 知识卡片数据方案评估'),
        ('D', 6, '软考刷题 App 知识卡片数据方案评估'),
    ], 22.5))
    # Row 2: Subtitle (merged A2:D2)
    rows.append((2, [
        ('A', 10, '基于《软考刷题App PRD V1.7》与《数据设计文档 V1.2》的知识卡片相关数据结构整理。本版本已补全用户对象、真题卷、主知识点标注和 schema 版本。'),
        ('B', 10, '基于《软考刷题App PRD V1.7》与《数据设计文档 V1.2》的知识卡片相关数据结构整理。本版本已补全用户对象、真题卷、主知识点标注和 schema 版本。'),
        ('C', 10, '基于《软考刷题App PRD V1.7》与《数据设计文档 V1.2》的知识卡片相关数据结构整理。本版本已补全用户对象、真题卷、主知识点标注和 schema 版本。'),
        ('D', 10, '基于《软考刷题App PRD V1.7》与《数据设计文档 V1.2》的知识卡片相关数据结构整理。本版本已补全用户对象、真题卷、主知识点标注和 schema 版本。'),
    ], 18))
    # Row 4: Header
    rows.append((4, [
        ('A', 14, '维度'), ('B', 14, '结论'), ('C', 14, '说明'), ('D', 14, '建议/备注'),
    ], 22.5))

    data = [
        ('总体结论', '合理，可落地，V1.1 已补全缺口',
         'JSON + Markdown 双文件方案适合知识卡片场景。V1.1 补全用户表、真题卷、主知识点标注、schema_version、options 细化结构。',
         '持续推进 PRD 与数据设计对齐。'),
        ('优点', '静态/动态分层清晰',
         '静态元数据、正文、学习记录分开，职责边界明确。',
         '利于缓存、同步和离线优先。'),
        ('优点', '内容与渲染解耦',
         'JSON 只存可查询字段，MD 负责正文表达。',
         'Git diff 更干净，运营编辑友好。'),
        ('优点', '关系设计完整',
         '前置、关联、题目、掌握度、用户都能挂起来。',
         '对"背卡片 → 做题 → 复盘"闭环友好。'),
        ('优点', '渲染约定明确',
         '==重点==、:::tip/warning/key:::、表格注释都定义了。',
         '实现成本可控。'),
        ('V1.1 改进', '补全用户对象 (users)',
         'PRD 12.1 定义的用户字段正式纳入数据字典，含 login_status、exam_date、weekly_days、daily_minutes。',
         '支撑考试日期驱动任务量和周报生成。'),
        ('V1.1 改进', '补全真题卷 (exam_paper)',
         '新增 paper 对象定义，支撑历年真题卷入口和 paper 类型学习记录。',
         '标记为 V1.5 完善，V1 最小字段先行。'),
        ('V1.1 改进', '细化 knowledge_point_ids 结构',
         '从模糊 json 改为 [{"point_id":"...","is_primary":bool}] 结构，支撑主知识点 60% 权重计算 (PRD 11.2)。',
         '同时细化 options 为 [{"key":"A","text":"..."}]。'),
        ('V1.1 改进', '补 schema_version 与 subject_id',
         'kp_*.json 新增 schema_version；chapter_meta.json 新增 subject_id，预留多科目扩展 (PRD 11.5)。',
         '降低未来迁移成本。'),
        ('风险', 'PRD 与设计仍存细微差异',
         'PRD 12.2 content 字段与设计文档 content_file 方案不一致，字典已做兼容标注。',
         '建议 PRD 下次修订时统一。'),
        ('风险', 'exam_paper 结构待完整定义',
         'V1 MVP 聚焦章节学习为主，真题卷的详细字段（如试卷总分、题型分布）需后续版本完善。',
         'V1 阶段按最小字段先行，避免过度设计。'),
        ('建议', '统一 PRD 12.2',
         '把知识点正文字段从 content 改写为 content_file + Markdown 正文。',
         '与数据设计保持一致。'),
        ('建议', '保持 synced 扩展字段',
         '学习记录 / 错题 / 任务中的 synced 字段保留，对离线同步很关键。',
         '设计文档扩展，已纳入字典。'),
        ('建议', '后续版本细化 exam_paper',
         'V1.5 或真题模块启动前，完善 paper 对象的题型分布、总分、时间限制等字段。',
         '避免 V1 阶段过度设计。'),
    ]
    for i, (dim, conclusion, desc, note) in enumerate(data):
        r = 5 + i
        rows.append((r, [
            ('A', 0, dim), ('B', 0, conclusion), ('C', 0, desc), ('D', 0, note),
        ]))

    return rows, [('A1:D1',), ('A2:D2',)]

# ── Sheet 2: 数据字典 (key changes) ──────────────────────────

def build_sheet2():
    """数据字典 sheet — 补全 users、exam_paper、细化字段结构"""
    rows = []

    # Row 1: Title (merged A1:K1)
    rows.append((1, [
        ('A', 6, '知识卡片与学习数据字典'), ('B', 6, '知识卡片与学习数据字典'),
        ('C', 6, '知识卡片与学习数据字典'), ('D', 6, '知识卡片与学习数据字典'),
        ('E', 6, '知识卡片与学习数据字典'), ('F', 6, '知识卡片与学习数据字典'),
        ('G', 6, '知识卡片与学习数据字典'), ('H', 6, '知识卡片与学习数据字典'),
        ('I', 6, '知识卡片与学习数据字典'), ('J', 6, '知识卡片与学习数据字典'),
        ('K', 6, '知识卡片与学习数据字典'),
    ], 22.5))
    # Row 2: Subtitle
    rows.append((2, [
        ('A', 10, '包含用户、静态索引、知识卡片元数据、题目、真题卷、学习记录、错题本、掌握度和每日任务等 10 类数据对象。'),
        ('B', 10, '包含用户、静态索引、知识卡片元数据、题目、真题卷、学习记录、错题本、掌握度和每日任务等 10 类数据对象。'),
        ('C', 10, '包含用户、静态索引、知识卡片元数据、题目、真题卷、学习记录、错题本、掌握度和每日任务等 10 类数据对象。'),
        ('D', 10, '包含用户、静态索引、知识卡片元数据、题目、真题卷、学习记录、错题本、掌握度和每日任务等 10 类数据对象。'),
        ('E', 10, '包含用户、静态索引、知识卡片元数据、题目、真题卷、学习记录、错题本、掌握度和每日任务等 10 类数据对象。'),
        ('F', 10, '包含用户、静态索引、知识卡片元数据、题目、真题卷、学习记录、错题本、掌握度和每日任务等 10 类数据对象。'),
        ('G', 10, '包含用户、静态索引、知识卡片元数据、题目、真题卷、学习记录、错题本、掌握度和每日任务等 10 类数据对象。'),
        ('H', 10, '包含用户、静态索引、知识卡片元数据、题目、真题卷、学习记录、错题本、掌握度和每日任务等 10 类数据对象。'),
        ('I', 10, '包含用户、静态索引、知识卡片元数据、题目、真题卷、学习记录、错题本、掌握度和每日任务等 10 类数据对象。'),
        ('J', 10, '包含用户、静态索引、知识卡片元数据、题目、真题卷、学习记录、错题本、掌握度和每日任务等 10 类数据对象。'),
        ('K', 10, '包含用户、静态索引、知识卡片元数据、题目、真题卷、学习记录、错题本、掌握度和每日任务等 10 类数据对象。'),
    ], 18))
    # Row 4: Header
    rows.append((4, [
        ('A', 14, '模块'), ('B', 14, '对象'), ('C', 14, '对象描述'),
        ('D', 14, '字段'), ('E', 14, '类型'), ('F', 14, '必填'),
        ('G', 14, '主键'), ('H', 14, '约束/枚举'), ('I', 14, '说明'),
        ('J', 14, '来源'), ('K', 14, '备注'),
    ], 22.5))

    # ── Data rows ──
    row_num = 5

    def add_data(module, obj, desc, fields):
        nonlocal row_num
        first = True
        for (field, ftype, required, pk, constraint, note, source, remark) in fields:
            rows.append((row_num, [
                ('A', 0, module if first else ''),
                ('B', 0, obj if first else ''),
                ('C', 0, desc if first else ''),
                ('D', 0, field), ('E', 0, ftype), ('F', 0, required),
                ('G', 0, pk), ('H', 0, constraint), ('I', 0, note),
                ('J', 0, source), ('K', 0, remark),
            ]))
            first = False
            row_num += 1

    # ★ NEW: 用户账号
    add_data('用户账号', 'users', '用户账号与备考配置表，存储用户身份、考试日期和学习偏好，驱动任务生成与周报。',
        [('user_id', 'string', '是', '是', '-', '用户唯一标识', 'PRD 12.1', ''),
         ('login_status', 'enum', '是', '否', 'guest / login / vip', '登录状态', 'PRD 12.1', '三级权限漏斗'),
         ('subject_id', 'string', '是', '否', '-', '当前学习科目 ID', 'PRD 12.1', 'V1 固定为高项'),
         ('exam_date', 'date', '是', '否', 'YYYY-MM-DD', '预计考试日期', 'PRD 12.1', '驱动倒计时与任务量'),
         ('weekly_days', 'int', '是', '否', '1-7', '每周计划学习天数', 'PRD 12.1', '用于生成每日任务'),
         ('daily_minutes', 'int', '是', '否', '> 0', '每日学习分钟数', 'PRD 12.1', '用于估算日任务量')])

    # 静态索引 — subject_index (no changes)
    add_data('静态索引', 'subject_index.json', '科目总索引，承载科目基础信息和章节摘要，用于首页/目录快速加载。',
        [('subject_id', 'string', '是', '是', '-', '科目唯一标识', '设计 1.3 / 1.4 / 2.1', ''),
         ('subject_name', 'string', '是', '否', '-', '科目名称', '设计 1.3 / 1.4 / 2.1', ''),
         ('chapters', 'array<chapter_summary>', '是', '否', '数组项含 chapter_id / title / card_count', '章节列表摘要', '设计 1.3 / 1.4 / 2.1', '用于首页/目录快速加载'),
         ('chapters[].chapter_id', 'string', '是', '否', '-', '章节 ID', '设计 1.3 / 1.4 / 2.1', ''),
         ('chapters[].title', 'string', '是', '否', '-', '章节标题', '设计 1.3 / 1.4 / 2.1', ''),
         ('chapters[].card_count', 'int', '是', '否', '>= 0', '该章节卡片数', '设计 1.3 / 1.4 / 2.1', '')])

    # ★ UPDATED: chapter_meta — added subject_id
    add_data('静态索引', 'chapter_meta.json', '章节元数据，描述章节标题、排序和概要信息，是章节树的上层索引。',
        [('chapter_id', 'string', '是', '是', '-', '章节唯一标识', '设计 1.3 / 1.4 / 2.1', ''),
         ('subject_id', 'string', '是', '否', '-', '所属科目 ID，预留多科目扩展 (PRD 11.5)', '设计 1.3 ★ V1.1新增', ''),
         ('title', 'string', '是', '否', '-', '章节标题', '设计 1.3 / 1.4 / 2.1', ''),
         ('description', 'string', '否', '否', '-', '章节描述', '设计 1.3 / 1.4 / 2.1', ''),
         ('sort_no', 'int', '是', '否', '>= 0', '章节排序号', '设计 1.3 / 1.4 / 2.1', ''),
         ('sections', 'array<section_summary>', '是', '否', '数组项含 section_id / title / sort_no / description / card_count', '子章节摘要列表，用于章节目录树三级渲染 ★ V1.4 新增', '数据字典 V1.4', '')])

    # Knowledge card meta — unchanged structure
    add_data('静态知识卡片', 'knowledge_card_meta (kp_*.json)', '知识卡片元数据，描述单张知识卡片的可检索属性、关联关系和正文引用。',
        [('point_id', 'string', '是', '是', '-', '知识点唯一标识', '设计 1.3 / 1.4 / 2.1', ''),
         ('subject_id', 'string', '是', '否', '-', '科目 ID', '设计 1.3 / 1.4 / 2.1', ''),
         ('chapter_id', 'string', '是', '否', '-', '所属章节 ID', '设计 1.3 / 1.4 / 2.1', ''),
         ('section_id', 'string', '是', '否', '如 sec_01_01', '所属子章节 ID，与 chapter_meta.sections[].section_id 对应 ★ V1.4 新增', '数据字典 V1.4', ''),
         ('title', 'string', '是', '否', '<= 30 字', '卡片标题', '设计 1.3 / 1.4 / 2.1', ''),
         ('card_type', 'enum', '是', '否', 'concept / process / comparison / formula / definition', '卡片类型', '设计 1.3 / 1.4 / 2.1', ''),
         ('difficulty', 'int', '是', '否', '1-3', '内容难度，与题目难度对齐', '设计 1.3 / 1.4 / 2.1', ''),
         ('estimated_read_seconds', 'int', '否', '否', '> 0', '预估阅读时长', '设计 1.3 / 1.4 / 2.1', ''),
         ('has_key_content', 'bool', '是', '否', 'true / false', '是否存在 ==重点标注==', '设计 1.3 / 1.4 / 2.1', ''),
         ('is_free', 'bool', '是', '否', 'true / false', '是否免费可见', '设计 1.3 / 1.4 / 2.1', ''),
         ('sort_no', 'int', '是', '否', '>= 0', '章节内排序序号', '设计 1.3 / 1.4 / 2.1', ''),
         ('content_file', 'string', '是', '否', '如 kp_ch04_001.md', '正文 MD 文件名', '设计 1.3 / 1.4 / 2.1', ''),
         ('tags', 'string[]', '否', '否', '数组，如 ["信息","信息化"]', '关键词标签，用于分类检索与智能推荐 ★ V1.2 新增', '数据字典 V1.2', ''),
         ('key_points', 'string', '否', '否', 'Markdown 格式', '高频考点，渲染为正文下方独立蓝色卡片 ★ V1.5 新增', '数据字典 V1.4', '支持粗体、列表等基础 MD 语法'),
         ('mnemonics', 'string', '否', '否', 'Markdown 格式', '记忆口诀，渲染为考点卡片下方独立绿色卡片 ★ V1.5 新增', '数据字典 V1.4', '支持粗体、列表等基础 MD 语法'),
         ('prerequisite_point_ids', 'string[]', '否', '否', '数组', '前置知识点 ID', '设计 1.3 / 1.4 / 2.1', ''),
         ('related_point_ids', 'string[]', '否', '否', '数组', '关联知识点 ID', '设计 1.3 / 1.4 / 2.1', ''),
         ('related_question_ids', 'string[]', '否', '否', '数组', '关联题目 ID', '设计 1.3 / 1.4 / 2.1', ''),
         ('source', 'string', '否', '否', '-', '内容来源', '设计 1.3 / 1.4 / 2.1', ''),
         ('source_type', 'enum', '否', '否', 'official / public / original', '来源类型', '设计 1.3 / 1.4 / 2.1', ''),
         ('author', 'string', '否', '否', '-', '录入人', '设计 1.3 / 1.4 / 2.1', ''),
         ('reviewer', 'string', '否', '否', '-', '审核人', '设计 1.3 / 1.4 / 2.1', ''),
         ('created_at', 'datetime', '否', '否', 'ISO8601', '创建时间', '设计 1.3 / 1.4 / 2.1', ''),
         ('updated_at', 'datetime', '否', '否', 'ISO8601', '最后更新时间', '设计 1.3 / 1.4 / 2.1', ''),
         ('version', 'int', '否', '否', '>= 1', '内容版本号', '设计 1.3 / 1.4 / 2.1', ''),
         ('schema_version', 'int', '否', '否', '>= 1', 'JSON schema 版本号，用于内容校验与迁移 ★ V1.1 新增', '数据字典 V1.1', ''),
         ('content', 'richtext', '兼容', '否', '-', 'PRD 旧字段，已被正文 MD + content_file 取代', 'PRD 12.2 (旧)', 'PRD 旧字段；设计文档已改为双文件方案')])

    # ★ UPDATED: Question — refined knowledge_point_ids and options
    add_data('静态题目', 'question (ch_*_questions.json)', '章节题目集合，每章一个题目 JSON 文件，承载题干、选项、答案、解析和知识点关联。',
        [('question_id', 'string', '是', '是', '-', '题目唯一标识', 'PRD 12.2 - 12.6', ''),
         ('subject_id', 'string', '是', '否', '-', '科目 ID', 'PRD 12.2 - 12.6', ''),
         ('chapter_id', 'string', '是', '否', '-', '章节 ID', 'PRD 12.2 - 12.6', ''),
         ('knowledge_point_ids', 'json', '是', '否', '[{"point_id":"...","is_primary":bool}] ★ V1.1细化',
          '关联知识点数组，is_primary 标记主知识点（权重 60%，PRD 11.2）', 'PRD 12.2 - 12.6', ''),
         ('difficulty', 'int', '是', '否', '1-3', '题目难度', 'PRD 12.2 - 12.6', ''),
         ('year', 'int', '否', '否', '真题年份', '真题年份', 'PRD 12.2 - 12.6', ''),
         ('stem', 'text', '是', '否', '-', '题干', 'PRD 12.2 - 12.6', ''),
         ('options', 'json', '是', '否', '[{"key":"A","text":"..."}] ★ V1.1细化',
          '选项数组，key 为选项标号，text 为选项文字', 'PRD 12.2 - 12.6', ''),
         ('answer', 'string', '是', '否', '-', '正确答案', 'PRD 12.2 - 12.6', ''),
         ('analysis', 'text', '否', '否', '-', '解析', 'PRD 12.2 - 12.6', ''),
         ('is_free', 'bool', '是', '否', 'true / false', '是否免费可见', 'PRD 12.2 - 12.6', ''),
         ('domain_tags', 'json', '是', '否', '六维标签数组', '六维知识域标签，支撑雷达图', 'PRD 12.2 - 12.6', 'PRD 明确要求，设计文档未显式展开')])

    # ★ NEW: Exam Paper
    add_data('静态真题卷', 'exam_paper (papers/*.json)', '真题卷对象，承载历年真题卷的基础信息和题目引用。V1 MVP 阶段以章节学习为主，真题卷结构为最小定义。',
        [('paper_id', 'string', '是', '是', '-', '真题卷唯一标识', 'PRD 4.1 / 22.3', 'V1.5 完善'),
         ('subject_id', 'string', '是', '否', '-', '科目 ID', 'PRD 4.1', ''),
         ('title', 'string', '是', '否', '-', '真题卷标题（如"2024年11月 高项综合知识"）', 'PRD 4.1', ''),
         ('year', 'int', '是', '否', '-', '真题年份', 'PRD 4.1', ''),
         ('question_ids', 'string[]', '是', '否', '数组', '包含的题目 ID 列表（按试卷顺序）', 'PRD 4.1', ''),
         ('is_free', 'bool', '是', '否', 'true / false', '是否免费可见', 'PRD 12.6', 'Pro 买断可解锁全部真题'),
         ('total_score', 'int', '否', '否', '>= 0', '试卷总分', 'V1.5 完善', '')])

    # Dynamic data — user_records (no changes, but row numbers shift)
    add_data('动态数据', 'user_records', '用户学习记录表，记录阅读/答题过程中的位置、状态和耗时，用于断点续学与同步。',
        [('record_id', 'string', '是', '是', '-', '学习记录唯一标识', '设计 1.5 / 1.7', ''),
         ('user_id', 'string', '是', '否', '-', '用户 ID', '设计 1.5 / 1.7', ''),
         ('target_type', 'enum', '是', '否', 'point / question / paper', '目标类型', '设计 1.5 / 1.7', ''),
         ('target_id', 'string', '是', '否', '-', '目标 ID', '设计 1.5 / 1.7', ''),
         ('status', 'enum', '是', '否', 'not_start / doing / done', '学习状态', '设计 1.5 / 1.7', ''),
         ('last_position', 'string', '否', '否', '-', '最近学习位置', '设计 1.5 / 1.7', ''),
         ('answer_time_ms', 'int', '否', '否', '仅 question 记录', '答题耗时', '设计 1.5 / 1.7', ''),
         ('updated_at', 'datetime', '是', '否', 'ISO8601', '更新时间', '设计 1.5 / 1.7', ''),
         ('synced', 'int', '否', '否', '0 / 1', '同步标记，设计文档扩展字段', '设计 1.5 / 1.7', 'PRD 未显式列出')])

    # wrong_book
    add_data('动态数据', 'wrong_book', '错题本表，记录题目错因、复习优先级和艾宾浩斯下一次复习时间。',
        [('wrong_id', 'string', '是', '是', '-', '错题记录唯一标识', '设计 1.5 / 1.7', ''),
         ('user_id', 'string', '是', '否', '-', '用户 ID', '设计 1.5 / 1.7', ''),
         ('question_id', 'string', '是', '否', '-', '题目 ID', '设计 1.5 / 1.7', ''),
         ('wrong_count', 'int', '否', '否', '>= 1', '错误次数', '设计 1.5 / 1.7', ''),
         ('right_streak', 'int', '否', '否', '>= 0', '连续复习答对次数', '设计 1.5 / 1.7', ''),
         ('priority', 'enum', '是', '否', 'high / normal / archived', '复习优先级', '设计 1.5 / 1.7', ''),
         ('last_wrong_at', 'datetime', '是', '否', 'ISO8601', '最近答错时间', '设计 1.5 / 1.7', ''),
         ('next_review_at', 'datetime', '否', '否', 'ISO8601', '下次复习时间', '设计 1.5 / 1.7', '艾宾浩斯调度由客户端计算，服务端可纠偏'),
         ('synced', 'int', '否', '否', '0 / 1', '同步标记', '设计 1.5 / 1.7', '设计文档扩展字段')])

    # mastery_scores
    add_data('动态数据', 'mastery_scores', '掌握度表，按用户与知识点维度保存 0-100 分的学习掌握状态。',
        [('user_id', 'string', '是', '联合主键', '-', '用户 ID', '设计 1.5 / 1.7', ''),
         ('point_id', 'string', '是', '联合主键', '-', '知识点 ID', '设计 1.5 / 1.7', ''),
         ('score', 'int', '是', '否', '0-100', '掌握度分值', '设计 1.5 / 1.7', ''),
         ('updated_at', 'datetime', '是', '否', 'ISO8601', '更新时间', '设计 1.5 / 1.7', ''),
         ('synced', 'int', '否', '否', '0 / 1', '同步标记', '设计 1.5 / 1.7', '设计文档扩展字段')])

    # daily_tasks
    add_data('动态数据', 'daily_tasks', '每日计划任务表，保存每日微任务的目标数量、完成情况和状态。',
        [('task_id', 'string', '是', '是', '-', '任务唯一标识', '设计 1.5 / 1.7', ''),
         ('user_id', 'string', '是', '否', '-', '用户 ID', '设计 1.5 / 1.7', ''),
         ('task_date', 'date', '是', '否', 'YYYY-MM-DD', '任务日期', '设计 1.5 / 1.7', ''),
         ('task_type', 'enum', '是', '否', 'learn / practice / wrong_review', '任务类型', '设计 1.5 / 1.7', ''),
         ('target_id', 'string', '否', '否', '-', '关联章节或题单 ID', '设计 1.5 / 1.7', ''),
         ('target_count', 'int', '否', '否', '>= 0', '目标数量', '设计 1.5 / 1.7', ''),
         ('completed_count', 'int', '否', '否', '>= 0', '已完成数量', '设计 1.5 / 1.7', ''),
         ('status', 'enum', '是', '否', 'pending / doing / done / skipped', '任务状态', '设计 1.5 / 1.7', ''),
         ('synced', 'int', '否', '否', '0 / 1', '同步标记', '设计 1.5 / 1.7', '设计文档扩展字段')])

    return rows, [('A1:K1',), ('A2:K2',)]

# ── Sheet 3: 对象总览 (updated) ──────────────────────────────

def build_sheet3():
    """对象总览 sheet — 加入 users 和 exam_paper"""
    rows = []
    rows.append((1, [
        ('A', 6, '知识卡片相关数据对象总览'),
        ('B', 6, '知识卡片相关数据对象总览'),
        ('C', 6, '知识卡片相关数据对象总览'),
    ], 22.5))
    rows.append((2, [
        ('A', 10, '按对象层描述每类数据的职责、存放方式和使用场景。V1.1 新增用户和真题卷对象。'),
        ('B', 10, '按对象层描述每类数据的职责、存放方式和使用场景。V1.1 新增用户和真题卷对象。'),
        ('C', 10, '按对象层描述每类数据的职责、存放方式和使用场景。V1.1 新增用户和真题卷对象。'),
    ], 18))
    rows.append((4, [
        ('A', 14, '模块'), ('B', 14, '对象'), ('C', 14, '对象描述'),
    ], 22.5))

    data = [
        ('用户配置 ★新增', 'users', '用户账号与备考配置表，存储用户身份、考试日期和学习偏好，驱动任务生成与周报。'),
        ('静态索引', 'subject_index.json', '科目总索引，承载科目基础信息和章节摘要，用于首页/目录快速加载。'),
        ('静态索引', 'chapter_meta.json', '章节元数据，描述章节标题、排序和概要信息，是章节树的上层索引。含 subject_id 预留多科目。'),
        ('静态内容', 'knowledge_card_meta (kp_*.json)', '知识卡片元数据，描述单张知识卡片的可检索属性、关联关系和正文引用。'),
        ('静态内容', 'question (ch_*_questions.json)', '章节题目集合，每章一个题目 JSON 文件，承载题干、选项、答案、解析和知识点关联。'),
        ('静态内容 ★新增', 'exam_paper (papers/*.json)', '真题卷对象，承载历年真题卷基础信息和题目引用。V1 MVP 最小定义，V1.5 完善。'),
        ('动态数据', 'user_records', '用户学习记录表，记录阅读/答题过程中的位置、状态和耗时，用于断点续学与同步。'),
        ('动态数据', 'wrong_book', '错题本表，记录题目错因、复习优先级和艾宾浩斯下一次复习时间。'),
        ('动态数据', 'mastery_scores', '掌握度表，按用户与知识点维度保存 0-100 分的学习掌握状态。'),
        ('动态数据', 'daily_tasks', '每日计划任务表，保存每日微任务的目标数量、完成情况和状态。'),
    ]
    for i, (mod, obj, desc) in enumerate(data):
        r = 5 + i
        rows.append((r, [('A', 0, mod), ('B', 0, obj), ('C', 0, desc)]))

    return rows, [('A1:C1',), ('A2:C2',)]

# ── Sheet 4: 关系 (updated) ──────────────────────────────────

def build_sheet4():
    """关系 sheet — 新增用户和真题卷相关关系"""
    rows = []
    rows.append((1, [
        ('A', 6, '知识卡片相关实体关系'), ('B', 6, '知识卡片相关实体关系'),
        ('C', 6, '知识卡片相关实体关系'), ('D', 6, '知识卡片相关实体关系'),
        ('E', 6, '知识卡片相关实体关系'), ('F', 6, '知识卡片相关实体关系'),
    ], 22.5))
    rows.append((2, [
        ('A', 10, '说明静态内容、题目、用户、真题卷、掌握度、错题本和学习记录之间的引用方式。V1.1 新增用户和真题卷关系。'),
        ('B', 10, '说明静态内容、题目、用户、真题卷、掌握度、错题本和学习记录之间的引用方式。V1.1 新增用户和真题卷关系。'),
        ('C', 10, '说明静态内容、题目、用户、真题卷、掌握度、错题本和学习记录之间的引用方式。V1.1 新增用户和真题卷关系。'),
        ('D', 10, '说明静态内容、题目、用户、真题卷、掌握度、错题本和学习记录之间的引用方式。V1.1 新增用户和真题卷关系。'),
        ('E', 10, '说明静态内容、题目、用户、真题卷、掌握度、错题本和学习记录之间的引用方式。V1.1 新增用户和真题卷关系。'),
        ('F', 10, '说明静态内容、题目、用户、真题卷、掌握度、错题本和学习记录之间的引用方式。V1.1 新增用户和真题卷关系。'),
    ], 18))
    rows.append((4, [
        ('A', 14, '源对象'), ('B', 14, '源字段'), ('C', 14, '目标对象'),
        ('D', 14, '目标字段/规则'), ('E', 14, '关系类型'), ('F', 14, '说明'),
    ], 22.5))

    data = [
        ('subject_index.json', 'chapters[].chapter_id', 'chapter_meta.json', 'chapter_id', '1:N', '科目索引指向章节元数据'),
        ('chapter_meta.json', 'chapter_id', 'knowledge_card_meta', 'chapter_id', '1:N', '章节下挂知识卡片'),
        ('chapter_meta.json', 'chapter_id', 'question', 'chapter_id', '1:N', '章节下挂题目'),
        ('knowledge_card_meta', 'point_id', 'question', 'knowledge_point_ids[].point_id', 'N:M', '题目可关联 1~N 个知识点（含主知识点 is_primary）'),
        ('knowledge_card_meta', 'point_id', 'knowledge_card_meta', 'prerequisite_point_ids[] / related_point_ids[]', '自关联', '前置 / 关联知识点图谱'),
        ('question', 'question_id', 'knowledge_card_meta', 'related_question_ids[]', 'N:M', '背完即练跳转'),
        ('question', 'question_id', 'wrong_book', 'question_id', '1:N', '题目对应多个错题记录/复习轮次'),
        ('knowledge_card_meta', 'point_id', 'mastery_scores', 'point_id', '1:1 per user', '知识点掌握度'),
        ('user_records', 'target_type + target_id', 'point/question/paper', '-', '多态引用', '学习记录目标类型多态'),
        ('users ★新增', 'user_id', 'user_records', 'user_id', '1:N', '用户的学习记录'),
        ('users ★新增', 'user_id', 'wrong_book', 'user_id', '1:N', '用户的错题本'),
        ('users ★新增', 'user_id', 'mastery_scores', 'user_id', '1:N', '用户的掌握度'),
        ('users ★新增', 'user_id', 'daily_tasks', 'user_id', '1:N', '用户的每日任务'),
        ('subject_index.json ★新增', 'subject_id', 'exam_paper', 'subject_id', '1:N', '科目下的真题卷'),
        ('exam_paper ★新增', 'question_ids[]', 'question', 'question_id', '1:N', '真题卷包含的题目'),
    ]
    for i, (src, sfield, tgt, tfield, rel, desc) in enumerate(data):
        r = 5 + i
        rows.append((r, [
            ('A', 0, src), ('B', 0, sfield), ('C', 0, tgt),
            ('D', 0, tfield), ('E', 0, rel), ('F', 0, desc),
        ]))

    return rows, [('A1:F1',), ('A2:F2',)]

# ── Sheet 5: Markdown规则 (unchanged copy from original) ─────

def copy_sheet5(zf):
    """Copy sheet5 (Markdown规则) as-is from original."""
    return zf.read('xl/worksheets/sheet5.xml')

# ── Main ──────────────────────────────────────────────────────

def build_xlsx():
    with zipfile.ZipFile(SRC, 'r') as zf_in:
        with zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED) as zf_out:

            # Copy unchanged files
            unchanged = [
                '[Content_Types].xml', '_rels/.rels',
                'xl/styles.xml', 'xl/theme/theme1.xml',
                'xl/_rels/workbook.xml.rels',
            ]
            for name in unchanged:
                if name in zf_in.namelist():
                    zf_out.writestr(name, zf_in.read(name))

            # ── Column definitions (reuse from original) ──
            # Sheet 1 cols
            cols1 = ET.fromstring(zf_in.read('xl/worksheets/sheet1.xml')).find(f'{{{NS}}}cols')
            # Sheet 2 cols (11 columns)
            cols2 = ET.fromstring(zf_in.read('xl/worksheets/sheet2.xml')).find(f'{{{NS}}}cols')
            # Sheet 3 cols (3 columns)
            cols3 = ET.fromstring(zf_in.read('xl/worksheets/sheet3.xml')).find(f'{{{NS}}}cols')
            # Sheet 4 cols (6 columns)
            cols4 = ET.fromstring(zf_in.read('xl/worksheets/sheet4.xml')).find(f'{{{NS}}}cols')
            # Sheet 5 cols
            cols5 = ET.fromstring(zf_in.read('xl/worksheets/sheet5.xml')).find(f'{{{NS}}}cols')

            # ── Build sheets ──
            rows1, merges1 = build_sheet1()
            rows2, merges2 = build_sheet2()
            rows3, merges3 = build_sheet3()
            rows4, merges4 = build_sheet4()

            zf_out.writestr('xl/worksheets/sheet1.xml',
                sheet_xml(cols1, [xrow(*args) for args in rows1], merges1))
            zf_out.writestr('xl/worksheets/sheet2.xml',
                sheet_xml(cols2, [xrow(*args) for args in rows2], merges2))
            zf_out.writestr('xl/worksheets/sheet3.xml',
                sheet_xml(cols3, [xrow(*args) for args in rows3], merges3))
            zf_out.writestr('xl/worksheets/sheet4.xml',
                sheet_xml(cols4, [xrow(*args) for args in rows4], merges4))
            # Sheet 5 unchanged
            zf_out.writestr('xl/worksheets/sheet5.xml', copy_sheet5(zf_in))

            # ── Workbook (unchanged sheet names/ids) ──
            zf_out.writestr('xl/workbook.xml', zf_in.read('xl/workbook.xml'))

    print(f'✅ 已生成: {DST}')
    print(f'   Sheet 1 (评估): 更新评估结论，标注改进项')
    print(f'   Sheet 2 (数据字典): 新增 users (6字段)、exam_paper (7字段)、chapter_meta.subject_id、kp_*.schema_version、kp_*.tags')
    print(f'   Sheet 2 (数据字典): 细化 knowledge_point_ids → [{{"point_id","is_primary"}}]、options → [{{"key","text"}}]')
    print(f'   Sheet 3 (对象总览): 新增 users、exam_paper 对象')
    print(f'   Sheet 4 (关系): 新增 7 条用户和真题卷相关关系')

if __name__ == '__main__':
    build_xlsx()
