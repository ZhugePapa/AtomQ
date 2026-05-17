# AtomQ Data Storage Policy

本文档定义 `data/` 目录中各类数据的线上存放位置、App 内缓存方式，以及 Supabase 云端同步边界。

当前结论：

- 公共读免费静态内容只发布本地 `data/content_package/public/`，线上放到阿里 OSS 的 `atomq/content_package/public/`，App 统一通过阿里 CDN 读取。
- 完整静态内容源目录 `data/content_package/` 不能直接公共读发布，因为其中可能包含 `is_free = false` 的付费内容。
- 用户动态数据走 App 本地 SQLite + Supabase Postgres 同步。
- App Bundle 只内置最小兜底内容。
- 内容生产资料和构建脚本不发布到线上运行环境。

## 1. 总体原则

| 数据类型 | 主存放位置 | App 内位置 | 是否进 Supabase Postgres | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| 免费静态 JSON 元数据 | 阿里 OSS 公共读 + 阿里 CDN | `Documents/cache/cards/content_package/public/`，并保留 Bundle 兜底 | 否 | 只发布 `is_free = true` 的内容 |
| 免费 Markdown 正文 | 阿里 OSS 公共读 + 阿里 CDN | `Documents/cache/cards/content_package/public/`，并保留 Bundle 兜底 | 否 | 与 JSON 同目录发布，通过 `content_file` 关联 |
| 免费题库 JSON | 阿里 OSS 公共读 + 阿里 CDN | `Documents/cache/cards/content_package/public/`，首章可 Bundle 兜底 | 否 | 只包含免费题目，公共读不放付费题 |
| 完整静态内容源 | 本地仓库/内容生产环境 | 不直接进入公共读缓存 | 否 | `data/content_package/` 是源目录，不是公共发布目录 |
| 用户动态数据 | Supabase Postgres | `Documents/data.db` | 是 | 学习记录、错题、掌握度、任务、标熟、收藏、笔记 |
| UI 轻量偏好 | 本机 | `UserDefaults` | 否 | 如重点显示/隐藏开关，不作为业务同步数据 |

一句话落地：

```text
免费静态内容按 public 文件包发布到阿里 OSS，App 通过阿里 CDN 读取。
动态用户行为进入 SQLite + Supabase。
App 首包只带最小可用兜底内容。
```

## 2. 当前 data 目录归属

| 当前路径 | 内容 | 线上归属 | App 内归属 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `data/content_package/public/manifest.json` | 公开免费内容包版本、章节数量、schema 版本 | 阿里 OSS 公共读 + 阿里 CDN | 沙盒缓存，Bundle 可放兜底版 | App 用于版本比对、增量更新 |
| `data/content_package/public/file_index.json` | 公开免费内容文件清单 | 阿里 OSS 公共读 + 阿里 CDN | 沙盒缓存 | App 按清单下载，不依赖 OSS 目录列表 |
| `data/content_package/public/subjects/*/subject_index.json` | 公开免费科目索引 | 阿里 OSS 公共读 + 阿里 CDN | 沙盒缓存 + Bundle 兜底 | 包含全部可发布章节 |
| `data/content_package/public/subjects/*/chapters/*/chapter_meta.json` | 公开免费章节与子章节结构 | 阿里 OSS 公共读 + 阿里 CDN | 沙盒缓存 + Bundle 兜底 | 小节 `card_count` 对应全部公开内容 |
| `data/content_package/public/subjects/*/chapters/*/cards/*.json` | 公开免费知识卡片元数据 | 阿里 OSS 公共读 + 阿里 CDN | 沙盒缓存 + Bundle 兜底 | 所有卡片均为 `is_free = true` |
| `data/content_package/public/subjects/*/chapters/*/cards/*.md` | 公开免费知识卡片正文 | 阿里 OSS 公共读 + 阿里 CDN | 沙盒缓存 + Bundle 兜底 | 所有正文均可公开访问 |
| `data/content_package/public/subjects/*/questions/*.json` | 公开免费章节题目 | 阿里 OSS 公共读 + 阿里 CDN | 沙盒缓存，首章可 Bundle 兜底 | 所有题目均为 `is_free = true` |
| `data/local_store/schema.sql` | 本地动态库 schema | 不直接发布为内容包 | App SQLite 建表依据 | Supabase migration 可参考同类结构 |
| `data/sources/source_manifest.json` | 内容来源、PDF 路径、抽取说明 | 不发布 | 不打进 App | 包含本机路径和生产说明，仅仓库内部使用 |
| `data/scripts/*` | 内容构建与校验脚本 | 不发布 | 不打进 App | 仅内容生产或 CI 使用 |
| `data/.old/` | 历史备份 | 不发布 | 不打进 App | 旧数据和旧脚本，仅参考 |

## 3. 公共读免费内容包规则

`data/content_package/public/` 是唯一可发布的公共读免费内容包。完整包已移除，当前所有静态卡片与题目均进入公开免费包。

发布包需要满足：

- 所有知识卡片 JSON 与对应 Markdown 都位于 `data/content_package/public/subjects/` 下。
- 所有卡片与题目的 `is_free` 均为 `true`。
- `subject_index.json` 和 `chapter_meta.json` 中的数量对应全部公开内容。
- `file_index.json` 包含所有发布文件，让 App 不依赖 OSS 目录列表。
- 正文 `.md` 不包含 `:::key`、`:::tip`、`:::warning`；这些内容应在同名 `.json` 的 `key_points`、`mnemonics`、`warnings` 字段中。

推荐线上路径结构保持与本地一致：

```text
content_package/public/
├── manifest.json
├── file_index.json
└── subjects/
    └── high_itpmp/
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
- 公共读 OSS 只能上传本地 `data/content_package/public/` 到线上 `atomq/content_package/public/`，不能上传完整 `content_package/`。
- `file_index.json` 必须与线上文件保持一致。
- App 启动或进入内容页时，先比对 `manifest.json`。
- 新版本内容按文件增量下载到沙盒缓存。
- 静态 JSON / MD / question 文件不写入 Supabase Postgres。
- 如未来需要后台 CMS 检索，可以另建服务端索引，但客户端仍以 CDN 文件包为主。

当前 CDN 访问阶段：

- OSS Bucket 可配置公共读，只用于免费内容。
- App 配置 `ATOMQ_PUBLIC_CONTENT_BASE_URL` 为 CDN 上 `atomq/content_package/public/` 的 HTTPS 根地址。
- 当前 CDN 地址为 `https://atomq.leoht.space/atomq/content_package/public/`。
- OSS 直连源站地址保留为 `https://leoht.oss-cn-beijing.aliyuncs.com/atomq/content_package/public/`，仅用于排查回源和权限问题。
- 免费公开内容不需要签名 URL、用户 Token、临时凭证或本地签名服务。
- 不在 App 内放阿里云 AccessKey、Secret、STS Token。

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
    ├── cache/cards/content_package/public/  # OSS/CDN 下载的免费静态内容缓存
    └── data.db                              # 用户动态数据 SQLite
```

读取优先级：

1. `Documents/cache/cards/content_package/public/`
2. `Bundle/Resources/default_cards/`
3. 阿里 OSS/CDN 下载后写入 `Documents/cache/cards/content_package/public/`

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
| `users` | `data/local_store/schema.sql` | 用户身份、当前科目、考试日期、学习计划参数、当前启用计划 |
| `study_plans` | `data/local_store/schema.sql` | 学习计划规则、生成时内容快照、每日卡片/题目目标 |
| `user_records` | `data/local_store/schema.sql` | 阅读/答题状态、断点续学、答题耗时 |
| `wrong_book` | `data/local_store/schema.sql` | 错题本、错误次数、复习优先级、下次复习时间 |
| `mastery_scores` | `data/local_store/schema.sql` | 用户对知识点的 0-100 掌握度 |
| `daily_tasks` | `data/local_store/schema.sql` | 每日学习、练习、错题复习任务 |
| `daily_study_stats` | `data/local_store/schema.sql` | 按天汇总学习时长、学习卡片数、刷题数、打卡状态 |

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

- `data/content_package/` 中的 `is_free = false` 内容
- `data/.old/`
- `data/scripts/`
- `data/scripts/__pycache__/`
- `data/sources/source_manifest.json` 中的本机绝对路径
- 临时抽取文本、调试脚本、旧 SQLite 文件
- `.DS_Store`
- 任何包含 API Key、Token、私有路径或版权未确认原文的文件

## 7. 发布检查清单

公共读免费静态内容发布检查：

- `manifest.json` 的 `content_version` 已更新。
- `schema_version` 与客户端解析模型兼容。
- OSS 公共读目录上传的是本地 `data/content_package/public/` 对应的线上 `atomq/content_package/public/`。
- `file_index.json` 已上传，并且包含所有公开文件。
- 公共读目录中不存在 `is_free = false` 的 JSON。
- 所有 `content_file` 都能在同目录找到对应 `.md` 文件。
- 所有 `related_question_ids` 和 `knowledge_point_ids` 可解析。
- 不包含 `sources/`、`scripts/`、`.old/`、`__pycache__/`。

上线 Supabase 前检查：

- `users`、`study_plans`、`user_records`、`wrong_book`、`mastery_scores`、`daily_tasks`、`daily_study_stats` 已建表。
- RLS 已启用并按 `user_id` 限制访问。
- 登录态和本地游客态有清晰合并策略。
- App 离线时可正常学习和答题。
- 网络恢复后能从 `synced = 0` 数据补传。

## 8. 推荐最终架构

```text
阿里 OSS 公共读，备案后阿里 CDN
└── atomq/content_package/public/
    ├── manifest.json
    ├── file_index.json
    ├── subject_index.json
    ├── chapter_meta.json
    ├── cards/*.json
    ├── cards/*.md
    └── questions/*.json

iOS App
├── Bundle default_cards/                         # 最小兜底内容
├── Documents/cache/cards/content_package/public/ # 免费静态内容缓存
├── Documents/data.db                             # 动态数据 SQLite
└── UserDefaults                                  # 轻量 UI 偏好

Supabase
└── Postgres                                      # 用户动态数据云同步
```

核心判断标准：

```text
会随内容版本变化、对所有用户基本一致的数据 -> content_package/public -> OSS/CDN。
会随用户行为变化、需要跨设备恢复的数据 -> SQLite + Supabase。
首启无网络也必须可用的最小内容 -> App Bundle。
公共读阶段只发布免费内容 -> content_package/public。
```
