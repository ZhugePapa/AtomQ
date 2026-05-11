# AtomQ Data Storage Policy

本文档定义 `data/` 目录中各类数据的线上存放位置、App 内缓存方式，以及 Supabase 云端同步边界。

当前结论：

- 静态内容资产走阿里 OSS + 阿里 CDN。
- 用户动态数据走 App 本地 SQLite + Supabase Postgres 同步。
- App Bundle 只内置最小兜底内容。
- 内容生产资料和构建脚本不发布到线上运行环境。

## 1. 总体原则

| 数据类型 | 主存放位置 | App 内位置 | 是否进 Supabase Postgres | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| 静态 JSON 元数据 | 阿里 OSS + 阿里 CDN | `Documents/cache/cards/`，并保留 Bundle 兜底 | 否 | 内容资产，读多写少，适合版本化文件分发 |
| Markdown 正文 | 阿里 OSS + 阿里 CDN | `Documents/cache/cards/`，并保留 Bundle 兜底 | 否 | 与 JSON 同目录发布，通过 `content_file` 关联 |
| 题库 JSON | 阿里 OSS + 阿里 CDN | `Documents/cache/cards/`，首章可 Bundle 兜底 | 否 | 题库属于内容资产，不建议每次从数据库查询 |
| 用户动态数据 | Supabase Postgres | `Documents/data.db` | 是 | 学习记录、错题、掌握度、任务、标熟、收藏、笔记 |
| UI 轻量偏好 | 本机 | `UserDefaults` | 否 | 如重点显示/隐藏开关，不作为业务同步数据 |

一句话落地：

```text
静态内容按文件包走阿里 CDN。
动态用户行为进入 SQLite + Supabase。
App 首包只带最小可用兜底内容。
```

## 2. 当前 data 目录归属

| 当前路径 | 内容 | 线上归属 | App 内归属 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `data/content_package/manifest.json` | 内容包版本、章节数量、schema 版本 | 阿里 OSS + CDN | 沙盒缓存，Bundle 可放兜底版 | App 用于版本比对、增量更新 |
| `data/content_package/subjects/*/subject_index.json` | 科目索引 | 阿里 OSS + CDN | 沙盒缓存 + Bundle 兜底 | 首屏、目录快速加载 |
| `data/content_package/subjects/*/chapters/*/chapter_meta.json` | 章节与子章节结构 | 阿里 OSS + CDN | 沙盒缓存 + Bundle 兜底 | 章节树、卡片目录 |
| `data/content_package/subjects/*/chapters/*/cards/*.json` | 知识卡片元数据 | 阿里 OSS + CDN | 沙盒缓存 + Bundle 兜底 | 包含 `point_id`、`section_id`、`tags`、`key_points`、`mnemonics` 等 |
| `data/content_package/subjects/*/chapters/*/cards/*.md` | 知识卡片正文 | 阿里 OSS + CDN | 沙盒缓存 + Bundle 兜底 | Markdown 正文，不进 Supabase Postgres |
| `data/content_package/subjects/*/questions/*.json` | 章节题目 | 阿里 OSS + CDN | 沙盒缓存，首章可 Bundle 兜底 | 题干、选项、答案、解析、知识点关联 |
| `data/local_store/schema.sql` | 本地动态库 schema | 不直接发布为内容包 | App SQLite 建表依据 | Supabase migration 可参考同类结构 |
| `data/sources/source_manifest.json` | 内容来源、PDF 路径、抽取说明 | 不发布 | 不打进 App | 包含本机路径和生产说明，仅仓库内部使用 |
| `data/scripts/*.py` | 内容构建与校验脚本 | 不发布 | 不打进 App | 仅内容生产或 CI 使用 |
| `data/.old/` | 历史备份 | 不发布 | 不打进 App | 旧数据和旧脚本，仅参考 |

## 3. CDN 内容包规则

`data/content_package/` 是可发布的静态内容包源目录。发布时上传到阿里 OSS，并通过阿里 CDN 分发。

推荐线上路径结构保持与本地一致：

```text
content_package/
├── manifest.json
└── subjects/
    └── subj_high_level/
        ├── subject_index.json
        ├── chapters/
        │   └── ch_01/
        │       ├── chapter_meta.json
        │       └── cards/
        │           ├── ch_01_sec_01_001.json
        │           └── ch_01_sec_01_001.md
        └── questions/
            └── ch_01_questions.json
```

发布规则：

- `manifest.json` 必须包含 `content_version`、`generated_at`、`schema_version`。
- App 启动或进入内容页时，先比对 `manifest.json`。
- 新版本内容按文件增量下载到沙盒缓存。
- 静态 JSON / MD / question 文件不写入 Supabase Postgres。
- 如未来需要后台 CMS 检索，可以另建服务端索引，但客户端仍以 CDN 文件包为主。

## 4. App 内存放规则

App 内采用三层结构。

```text
App Bundle
└── Resources/default_cards/
    ├── manifest.json
    ├── subject_index.json
    └── 至少首章部分 JSON / MD / questions

App 沙盒
└── Documents/
    ├── cache/cards/       # CDN 下载的静态内容缓存
    └── data.db            # 用户动态数据 SQLite
```

读取优先级：

1. `Documents/cache/cards/`
2. `Bundle/Resources/default_cards/`
3. 阿里 CDN 下载后写入 `Documents/cache/cards/`

动态数据写入规则：

- 用户操作先写本地 SQLite。
- 动态表行带 `synced` 标记。
- 网络恢复后后台同步到 Supabase。
- App 不等待 Supabase 才允许刷题或阅读。

## 5. Supabase 存放规则

Supabase 只承载云端动态数据，不承载知识库静态文件。

当前应在 Supabase Postgres 中建立的正式动态表：

| 表 | 来源 | 用途 |
| :--- | :--- | :--- |
| `users` | `data/local_store/schema.sql` | 用户身份、当前科目、考试日期、学习计划参数 |
| `user_records` | `data/local_store/schema.sql` | 阅读/答题状态、断点续学、答题耗时 |
| `wrong_book` | `data/local_store/schema.sql` | 错题本、错误次数、复习优先级、下次复习时间 |
| `mastery_scores` | `data/local_store/schema.sql` | 用户对知识点的 0-100 掌握度 |
| `daily_tasks` | `data/local_store/schema.sql` | 每日学习、练习、错题复习任务 |

建议补充的动态表：

| 表 | 用途 |
| :--- | :--- |
| `user_card_states` | 用户对知识卡片的学习状态、标熟状态、首次/最近标熟时间 |
| `practice_sessions` | 巩固练习、每日一练等一次练习会话 |
| `practice_session_items` | 会话内题目明细、排序、关联知识点、作答状态 |
| `favorites` | 收藏知识卡、题目、试卷等目标对象 |
| `user_notes` | 用户对知识卡、题目或局部锚点的笔记 |

Supabase 同步原则：

- 登录用户按 `user_id` 做 RLS 隔离。
- App 本地 SQLite 是交互主写入点。
- Supabase 是云端备份、多端恢复和纠偏来源。
- 冲突处理优先使用 `updated_at`，错题调度可由云端纠偏 `next_review_at`。
- `synced` 是本地同步状态字段，云端可不保留，或保留为调试字段。

## 6. 不应发布的内容

以下内容不得上传到 CDN，不得打进 App，也不应进入 Supabase：

- `data/.old/`
- `data/scripts/`
- `data/scripts/__pycache__/`
- `data/sources/source_manifest.json` 中的本机绝对路径
- 临时抽取文本、调试脚本、旧 SQLite 文件
- `.DS_Store`
- 任何包含 API Key、Token、私有路径或版权未确认原文的文件

## 7. 发布检查清单

发布静态内容前检查：

- `manifest.json` 的 `content_version` 已更新。
- `schema_version` 与客户端解析模型兼容。
- 所有 `content_file` 都能在同目录找到对应 `.md` 文件。
- 所有 `related_question_ids` 和 `knowledge_point_ids` 可解析。
- `data/scripts/validate_content.py` 校验通过。
- 不包含 `sources/`、`scripts/`、`.old/`、`__pycache__/`。

上线 Supabase 前检查：

- `users`、`user_records`、`wrong_book`、`mastery_scores`、`daily_tasks` 已建表。
- RLS 已启用并按 `user_id` 限制访问。
- 登录态和本地游客态有清晰合并策略。
- App 离线时可正常学习和答题。
- 网络恢复后能从 `synced = 0` 数据补传。

## 8. 推荐最终架构

```text
阿里 OSS + 阿里 CDN
└── content_package/
    ├── manifest.json
    ├── subject_index.json
    ├── chapter_meta.json
    ├── cards/*.json
    ├── cards/*.md
    └── questions/*.json

iOS App
├── Bundle default_cards/       # 最小兜底内容
├── Documents/cache/cards/      # 静态内容缓存
├── Documents/data.db           # 动态数据 SQLite
└── UserDefaults                # 轻量 UI 偏好

Supabase
└── Postgres                    # 用户动态数据云同步
```

核心判断标准：

```text
会随内容版本变化、对所有用户基本一致的数据 -> CDN。
会随用户行为变化、需要跨设备恢复的数据 -> SQLite + Supabase。
首启无网络也必须可用的最小内容 -> App Bundle。
```
