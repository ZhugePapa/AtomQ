# 软考刷题 App — 知识卡片与学习数据 UML 类图

> **版本**: V1.0 | **依据**: PRD V1.7 + 数据设计文档 V1.2 + 数据字典 V1.1 | **日期**: 2026-05-09

---

## 图一：静态内容层（JSON + Markdown）

```mermaid
classDiagram
direction LR

%% === 枚举 ===

class CardType {
    <<enumeration>>
    concept
    process
    comparison
    formula
    definition
}

class SourceType {
    <<enumeration>>
    official
    public
    original
}

%% === 核心类 ===

class SubjectIndex {
    <<subject_index.json>>
    +subject_id : string  PK
    +subject_name : string
    +chapters : ChapterSummary[]
}

class ChapterSummary {
    <<内嵌>>
    +chapter_id : string
    +title : string
    +card_count : int
}

class ChapterMeta {
    <<chapter_meta.json>>
    +chapter_id : string  PK
    +subject_id : string  FK 新增
    +title : string
    +description : string
    +sort_no : int
}

class KnowledgeCardMeta {
    <<kp_*.json>>
    +point_id : string  PK
    +subject_id : string  FK
    +chapter_id : string  FK
    +title : string  ≤30字
    +card_type : CardType
    +difficulty : int  1-3
    +estimated_read_seconds : int
    +has_key_content : bool
    +is_free : bool
    +sort_no : int
    +content_file : string
    +prerequisite_point_ids : string[]
    +related_point_ids : string[]
    +related_question_ids : string[]
    +source : string
    +source_type : SourceType
    +author : string
    +reviewer : string
    +created_at : datetime
    +updated_at : datetime
    +version : int
    +schema_version : int  新增
}

class Question {
    <<ch_*_questions.json>>
    +question_id : string  PK
    +subject_id : string  FK
    +chapter_id : string  FK
    +knowledge_point_ids : KnowledgePointRef[]  细化
    +difficulty : int  1-3
    +year : int
    +stem : text
    +options : OptionItem[]  细化
    +answer : string
    +analysis : text
    +is_free : bool
    +domain_tags : string[]
}

class ExamPaper {
    <<papers_*.json  V1.5>>
    +paper_id : string  PK
    +subject_id : string  FK
    +title : string
    +year : int
    +question_ids : string[]
    +is_free : bool
    +total_score : int
}

class KnowledgePointRef {
    <<内嵌>>
    +point_id : string
    +is_primary : bool
}

class OptionItem {
    <<内嵌>>
    +key : string  ABCD
    +text : string
}

%% === 关系 ===

SubjectIndex *-- ChapterSummary : chapters数组
SubjectIndex "1" --> "*" ChapterMeta : chapters[]
ChapterMeta "1" --> "*" KnowledgeCardMeta : chapter_id
ChapterMeta "1" --> "*" Question : chapter_id
SubjectIndex "1" --> "*" ExamPaper : subject_id
ExamPaper "1" --> "*" Question : question_ids

KnowledgeCardMeta "*" --> "*" KnowledgeCardMeta : 前置/关联 (自关联)
KnowledgeCardMeta "1" --> "*" Question : related_question_ids
Question "*" --> "*" KnowledgeCardMeta : knowledge_point_ids\n(1→N, 主知识点权重60%)

Question *-- KnowledgePointRef : knowledge_point_ids数组
Question *-- OptionItem : options数组

%% === 样式 ===

style KnowledgeCardMeta fill:#FFFDE7,stroke:#FBC02D
style Question fill:#E8F5E9,stroke:#4CAF50
style SubjectIndex fill:#E8F5E9,stroke:#4CAF50
style ChapterMeta fill:#E8F5E9,stroke:#4CAF50
style ExamPaper fill:#F3E5F5,stroke:#9C27B0
style KnowledgePointRef fill:#F5F5F5,stroke:#9E9E9E
style OptionItem fill:#F5F5F5,stroke:#9E9E9E
style ChapterSummary fill:#F5F5F5,stroke:#9E9E9E

%% === 注释 ===

note for KnowledgeCardMeta "双文件方案\ncontent_file → .md 正文\n同目录: kp_*.json ↔ kp_*.md"
note for KnowledgePointRef "主知识点权重 60%\n其余均分 40%"
```

---

## 图二：动态数据层（SQLite）

```mermaid
classDiagram
direction LR

%% === 枚举 ===

class LoginStatus {
    <<enumeration>>
    guest
    login
    vip
}

class TargetType {
    <<enumeration>>
    point
    question
    paper
}

class RecordStatus {
    <<enumeration>>
    not_start
    doing
    done
}

class WrongPriority {
    <<enumeration>>
    high
    normal
    archived
}

class TaskType {
    <<enumeration>>
    learn
    practice
    wrong_review
}

class TaskStatus {
    <<enumeration>>
    pending
    doing
    done
    skipped
}

%% === 核心类 ===

class User {
    <<users 表  新增>>
    +user_id : string  PK
    +login_status : LoginStatus
    +subject_id : string  FK
    +exam_date : date
    +weekly_days : int  1-7
    +daily_minutes : int
}

class UserRecord {
    <<user_records>>
    +record_id : string  PK
    +user_id : string  FK
    +target_type : TargetType
    +target_id : string
    +status : RecordStatus
    +last_position : string
    +answer_time_ms : int
    +updated_at : datetime
    +synced : int  0/1
}

class WrongBook {
    <<wrong_book>>
    +wrong_id : string  PK
    +user_id : string  FK
    +question_id : string  FK
    +wrong_count : int
    +right_streak : int
    +priority : WrongPriority
    +last_wrong_at : datetime
    +next_review_at : datetime
    +synced : int  0/1
}

class MasteryScore {
    <<mastery_scores>>
    +user_id : string  PK_FK
    +point_id : string  PK_FK
    +score : int  0-100
    +updated_at : datetime
    +synced : int  0/1
}

class DailyTask {
    <<daily_tasks>>
    +task_id : string  PK
    +user_id : string  FK
    +task_date : date
    +task_type : TaskType
    +target_id : string
    +target_count : int
    +completed_count : int
    +status : TaskStatus
    +synced : int  0/1
}

%% 外部类引用（虚线框 = 静态层）
class KnowledgeCardMeta_Ref {
    <<静态层: kp_*.json>>
    point_id
}
class Question_Ref {
    <<静态层: ch_*_questions.json>>
    question_id
}
class ExamPaper_Ref {
    <<静态层: papers_*.json>>
    paper_id
}

%% === 关系 ===

User "1" --> "*" UserRecord : user_id
User "1" --> "*" WrongBook : user_id
User "1" --> "*" MasteryScore : user_id
User "1" --> "*" DailyTask : user_id

Question_Ref "1" --> "*" WrongBook : question_id
KnowledgeCardMeta_Ref "1" --> "0..1" MasteryScore : point_id (per user)

UserRecord "0..*" ..> KnowledgeCardMeta_Ref : target_type=point
UserRecord "0..*" ..> Question_Ref : target_type=question
UserRecord "0..*" ..> ExamPaper_Ref : target_type=paper

%% === 样式 ===

style User fill:#F3E5F5,stroke:#9C27B0
style MasteryScore fill:#FFFDE7,stroke:#FBC02D
style WrongBook fill:#FFFDE7,stroke:#FBC02D
style UserRecord fill:#E3F2FD,stroke:#2196F3
style DailyTask fill:#E3F2FD,stroke:#2196F3

style KnowledgeCardMeta_Ref fill:#F5F5F5,stroke:#9E9E9E,stroke-dasharray:5
style Question_Ref fill:#F5F5F5,stroke:#9E9E9E,stroke-dasharray:5
style ExamPaper_Ref fill:#F5F5F5,stroke:#9E9E9E,stroke-dasharray:5

%% === 注释 ===

note for MasteryScore "掌握度: 0-100 (PRD 11.2)\n0-29薄弱 | 30-59学习中\n60-79已完成 | 80-100已掌握\n得分 = f(对错, 难度系数, 耗时系数, 知识点权重)"
note for WrongBook "艾宾浩斯周期 (PRD 11.8)\n1→2→4→7→15→30天\n连续3轮答对 → archived\nnext_review_at 客户端计算"
```

---

## 跨层总览

```
┌─────────────────────────────────────────────────┐
│                 静态内容层 (CDN)                   │
│  subject_index ──→ chapter_meta ──→ kp_*.json    │
│       │                │              │           │
│       │                └──→ question  │           │
│       │                      │  ↑     │           │
│       └──→ exam_paper ──────┘  │  └───┘           │
│                                 │  关联关系         │
├─────────────────────────────────┼─────────────────┤
│                 动态数据层 (SQLite)                 │
│  users ──→ user_records ──→ target_type多态       │
│    │           (断点续学)        ↓                 │
│    ├──→ wrong_book ←── question_id                │
│    ├──→ mastery_scores ←── point_id               │
│    └──→ daily_tasks                              │
└─────────────────────────────────────────────────┘
```
