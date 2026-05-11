# AtomQ Data

当前目录采用新结构：

- `.old/`：旧脚本、旧样例、旧 SQLite，保留作参考但不再作为可发布数据源。
- `content_package/`：可下发的静态内容包，包含科目索引、章节元数据、知识卡片 JSON/Markdown、章节题目 JSON。
- `local_store/`：客户端本地动态库 schema，存用户学习记录、错题、掌握度和每日任务。
- `sources/`：内容来源与抽取说明。
- `scripts/`：内容构建与校验脚本。

静态内容继续使用 JSON + Markdown；动态用户数据进入 SQLite。后续同步到云端时，`content_package` 走 CDN/Storage，`local_store` 对应表走 Supabase/Postgres。
